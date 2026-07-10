---
id: 2026-07-10T12-00-36Z-canvas-timeline-artifact-chain
date: "2026-07-10T12:00:36Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - backend
  - timeline
  - task-artifacts
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py
  - ai-pic-backend/tests/integration/test_timeline_pipeline_import_api.py
summary: Expose the exact Timeline artifact from a completed canvas Timeline task and verify the restored Timeline-to-Report handoff.
---

## User Prompt

继续完善无限画布功能；当前整体链路还是断的。可以拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- Give a completed canvas Timeline task an exact, versioned artifact reference.
- Preserve that reference through task refresh and full canvas restore.
- Verify that Report summarizes the restored Timeline execution evidence.

## Changes

- Returned the created or updated Timeline from the asynchronous pipeline body to its task wrapper.
- Replaced the generic `script:<id>:timeline_pipeline` task result with `timeline:<id>:v<version>`.
- Updated the Timeline pipeline integration test to assert the exact persisted Timeline identity and version.

## Validation

1. Focused checks:

- `cd ai-pic-backend && python -m pytest tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_timeline_pipeline_errors.py -q` -> pass, 2 tests.
- Corrected backend `python -m compileall -q` invocation -> pass.
- `cd ai-pic-backend && python run_tests.py quick --no-setup` -> pass, 2406 passed, 77 skipped, 20 deselected.
- `cd ai-pic-backend && pytest -q` -> pass, 2416 passed, 88 skipped.
- Repository docs, scoped contracts, and `git diff --check` -> pass.
- Scoped `pre-commit run --files ...` -> pass after Black reformatted the new assertion and the focused tests were rerun.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> pass; backend and frontend production images built locally without push.

2. Browser and runtime validation:

- Entry URL: `http://localhost:8089/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6` in the Codex in-app browser against the development Docker stack.
- Initial browser execution `Task #6275` reproduced the break: it completed but exposed only `script:130:timeline_pipeline`, so downstream consumers could not identify the Timeline version.
- After the fix and backend/worker restart, browser execution `Task #6276` completed with `result_file_path: timeline:71:v3`.
- Timeline `#71` version `3` resolved 6 of 20 video clips: the first clip used the July MiniMax candidate through `legacy_storyboard_timing`, and five short clips used `short_gap_neighbor`. The remaining 14 clips correctly stayed missing because only one storyboard video candidate exists.
- Executing Report summarized 19 canvas nodes and 9 task evidence records. Its persisted output included task IDs `6266, 6269, 6270, 6271, 6272, 6273, 6274, 6275, 6276`, provider/model counts, and task lineage.
- A full page reload restored the Report output and Timeline `Task #6276` with `result_file_path: timeline:71:v3`. Browser console contained no warnings or errors.
- Screenshot: `artifacts/runs/canvas-timeline-report-chain-20260710T1202Z/timeline-report-restored-full.jpg`.

3. Remaining chain boundary:

- Timeline and Report context propagation is now connected, but final rendering remains blocked by 14 clips without video assets. This change deliberately does not label those clips ready or fabricate coverage from a single candidate.

## Next Steps

- Generate or bind video assets for the 14 unresolved Timeline clips, then exercise the Timeline render path and verify the final output artifact.
- Define explicit partial-failure semantics for storyboard image candidates when one provider call fails but usable candidates are persisted.

## Linked Commits

Pending.
