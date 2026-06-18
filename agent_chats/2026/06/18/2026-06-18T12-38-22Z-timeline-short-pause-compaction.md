---
id: 2026-06-18T12-38-22Z-timeline-short-pause-compaction
date: "2026-06-18T12:38:22Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - timeline
  - backend
  - storyboard
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py
  - ai-pic-backend/app/services/script/production_storyboard.py
  - ai-pic-backend/app/services/timeline_import_repair.py
  - ai-pic-backend/app/services/timeline_import_service.py
  - ai-pic-backend/app/services/timeline_pipeline_runner.py
  - ai-pic-backend/app/services/timeline_pipeline_state.py
  - ai-pic-backend/app/services/timeline_spec_builder.py
  - ai-pic-backend/app/services/timeline_video_pause_policy.py
  - ai-pic-backend/tests/integration/test_timeline_pipeline_import_api.py
  - ai-pic-backend/tests/test_timeline_import_repair.py
  - ai-pic-backend/tests/test_timeline_import_service.py
  - ai-pic-backend/tests/test_timeline_video_pause_policy.py
  - ai-pic-backend/tests/unit/services/script/test_production_storyboard_timeline_import.py
summary: Compact short pause beats during Timeline video import so storyboard/video work is not split into subsecond clips.
---

## User Prompt

继续；optimize the Timeline/storyboard chain after inspecting `http://localhost:8089/episodes/a311119b110e46fbb346201656bccb5c/workspace?tab=storyboard&scriptId=30`, where Timeline 69 v4 had 52 video clips over 3 minutes and many 0.42s placeholder segments.

## Goals

- Stop short pause beats from becoming standalone Timeline video clips.
- Preserve full visual coverage by absorbing short contiguous pauses into the previous video clip.
- Keep long pauses as explicit visual time.
- Repair already-imported Timelines on the same audio version when they still contain short pause video clips.
- Keep the one-click Timeline pipeline and production storyboard chain on the same pause threshold.

## Changes

- Added `timeline_video_pause_policy.py` with the default 1500ms video pause threshold and short-pause absorption logic.
- Moved Timeline pipeline state helpers into `timeline_pipeline_state.py` so the main-chain runner stays within service file-size limits.
- Updated Timeline Spec import to build video clips from compacted video beats while leaving dialogue/subtitle clips tied to real dialogue beats.
- Added `absorbed_pause_beat_ids`, `absorbed_pause_ranges`, and `absorbed_pause_duration_ms` metadata on expanded video clips for traceability.
- Extended existing Timeline import repair detection so same-version imports update stale video tracks containing short pause clips instead of returning `skipped`.
- Passed `min_pause_duration_ms` through the one-click Timeline pipeline and production storyboard path.
- Updated and added backend regression tests for short pause compaction, same-version repair, pipeline threshold propagation, and production storyboard propagation.
- Re-imported the local current Timeline 69 from existing audio timeline data only; no AI provider or shot-plan generation was run for the repair.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/test_timeline_import_service.py tests/test_timeline_import_repair.py tests/test_timeline_video_pause_policy.py tests/integration/test_timeline_pipeline_import_api.py::test_process_timeline_pipeline_imports_audio_timeline_to_timeline_spec tests/unit/services/script/test_production_storyboard_timeline_import.py::test_auto_timeline_placeholders_imports_timeline_spec_and_checks_audio -q` -> pass, 10 tests.
- `cd ai-pic-backend && pytest tests/test_timeline_video_pause_policy.py -q` -> pass, 1 test after moving the regression into its own file.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed timeline/backend test files>` -> pass.
- `git diff --check -- <changed timeline/backend test files>` -> pass after removing a trailing blank line.
- `cd ai-pic-backend && python run_tests.py quick` -> blocked before tests by dependency resolution in the current Python 3.13 environment: `langchain-core==0.2.43` requires `pydantic>=2.7.4`, while the repo pins `pydantic==2.5.0`.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/episodes/a311119b110e46fbb346201656bccb5c/workspace?tab=storyboard&scriptId=30`
- User path: opened the local workspace, re-authenticated with the current `AGENTS.md` test account after session expiry, and inspected the storyboard support workspace.
- Before repair evidence from current page/data: Timeline 69 v4, 52 video clips, 16 clips below 0.5s, 18 below 1s, 29 below 2s, and 16 standalone pause video clips.
- Repair command evidence: direct backend service import returned `action=updated`; Timeline 69 moved to v5 with 36 video clips, 0 clips below 0.5s, 0 below 1s, and 16 absorbed pause beats.
- Browser result: refreshed workspace shows `Timeline 69 · v5`, `3 轨 · 68 clips`, `36 个 video clip`, min visible clip duration 1.14s, and no `视频 N` placeholder-title samples.
- Console: browser warning/error log list was empty for the verified page.
- Network/API: `GET /api/v1/timelines/69` returned HTTP 200 with version 5, total clips 68, video clips 36, short_lt_500=0, short_lt_1000=0, absorbed_pause_count=16.

3. Conflict signals and corrections:

- Initial assumption that UI density might be only a display problem was contradicted by the page stats and `timeline_spec_builder.py`, which imported every normalized beat into the video track.
- A parallel pytest run produced `sqlite3.OperationalError: attempt to write a readonly database`; reran the affected tests sequentially and they passed.
- The first contract check flagged oversized files after the new code/test additions; moved pause policy into a dedicated service and moved the new regression into a dedicated test file.

## Next Steps

- Consider a later cleanup to make the pause threshold visible in Timeline operator controls if users need per-run tuning.
- The current local Timeline 69 was repaired; other historical timelines with the same fragmentation pattern will repair on the next import path or explicit overwrite/re-import.

## Linked Commits

- This commit.
