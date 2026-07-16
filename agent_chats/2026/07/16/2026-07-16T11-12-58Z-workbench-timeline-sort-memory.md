---
id: 2026-07-16T11-12-58Z-workbench-timeline-sort-memory
date: "2026-07-16T11:12:58Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - workbench
  - backend
  - timeline
  - mysql
  - browser-validation
related_paths:
  - ai-pic-backend/app/repositories/timeline_repository.py
  - ai-pic-backend/tests/unit/repositories/test_timeline_repository.py
  - artifacts/runs/workbench-sort-memory-fix-20260716T1113Z/
  - artifacts/runs/episode49-timeline-video-track-20260716T1926Z/
summary: Keep large Timeline JSON specs out of latest and episode-list sorts so the workbench and episode Timeline video track load under the live MySQL sort-buffer limit.
---

## User Prompt

工作台现在出错

后续截图显示第 4 集 Timeline 虽有 36 段和 03:00 时长，但选中片段显示
“缺视频”，成片区域显示“无视频轨”。

## Goals

- Reproduce the current operator-workbench failure from the running application.
- Identify the backend root cause rather than treating the browser CORS message as
  the primary failure.
- Fix the shared latest-Timeline lookup without changing MySQL configuration or
  adding an emergency schema migration.
- Restore episode 49's canonical Timeline spec so the frontend does not fall back
  to the audio-only timeline.
- Validate the live API and visible workbench while preserving unrelated Canvas
  worktree changes.

## Changes

- Changed `TimelineRepository.get_latest_for_episode_script` to sort and select
  only `Timeline.id`, then load the complete Timeline by primary key.
- Added a repository regression test that captures SQL and asserts the ordered
  projection excludes the large `timelines.spec` JSON column.
- Changed `TimelineRepository.list_for_episode` to sort only Timeline identifiers,
  then load complete Timeline rows in the same order.
- Added a second SQL-capture regression test for the episode Timeline list path.
- Kept the fix in the shared repository method so workbench, Canvas, storyboard,
  import, and render callers use the same safe lookup.

## Validation

1. Reproduction and root cause:

- Authenticated Playwright reproduction opened `http://localhost:8090/` and showed
  `Failed to fetch`.
- Browser Console reported CORS because the direct backend response lacked CORS
  headers after an unhandled failure; direct authenticated
  `GET /api/v1/workbench/summary` returned HTTP 500.
- Running `WorkbenchService.summary_for_user(1)` inside `ai-video-backend` produced
  MySQL error `1038: Out of sort memory` from
  `get_latest_for_episode_script`.
- The failing Timeline row had a `491336`-byte JSON `spec`; MySQL
  `sort_buffer_size` was `262144`, and `EXPLAIN` showed `Using filesort`.
- The episode 49 screenshot had the same root cause on
  `GET /api/v1/episodes/49/timelines`: the endpoint returned HTTP 500 with MySQL
  error `1038: Out of sort memory`.
- Because that request failed, the frontend retained the episode audio timeline:
  it could display 36 dialogue-derived segments and 03:00 duration but had no
  selected Timeline spec, resolved videos, or render output.

2. Automated backend:

- `cd ai-pic-backend && pytest tests/unit/repositories/test_timeline_repository.py tests/integration/test_workbench_summary_api.py -v`
  -> `5 passed`.
- `cd ai-pic-backend && python run_tests.py quick`
  -> did not reach tests because the Python 3.13 dependency setup could not resolve
  repository pins: `pydantic==2.5.0` conflicts with
  `langchain-core==0.2.43` requiring `pydantic>=2.7.4`.
- `ruff check app/repositories/timeline_repository.py tests/unit/repositories/test_timeline_repository.py`
  -> passed.
- `git diff --check` for the two backend paths -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- Changed-file repository contract check -> passed.
- Scoped pre-commit backend gate -> `2218 passed, 59 skipped`.
- The scoped pre-commit command returned nonzero after the passing checks because
  ledger enforcement detected the unrelated existing Canvas ledger and another
  concurrent Canvas pre-commit modified the worktree while the backend hook ran.
  No unrelated changes were reverted or staged.
- `pytest -q --no-cov tests/unit/repositories/test_timeline_repository.py tests/test_timeline_api.py tests/test_timeline_lifecycle_api.py`
  -> `9 passed`.
- `ruff`, Black, isort with the Black profile, `git diff --check`, and the
  changed-file repository contract check all passed for the Timeline repository
  and regression test.
- `python scripts/check_repo_docs.py` passed.
- Full all-files pre-commit was not rerun for the follow-up because the shared
  worktree contains unrelated concurrent Canvas, provider, single-video, and
  Timeline UI changes. Equivalent changed-file formatting, repository contract,
  ledger, and targeted pytest checks were run without stashing those files.
- A full `pytest` run was attempted and stopped after 91 seconds because the
  unrelated shared-suite setup was failing with SQLite `attempt to write a
readonly database` / `disk I/O error`; at interruption it reported
  `8 failed, 54 passed, 26 skipped, 16 errors`.
- `BUILD_PUSH=false ./docker/build_prod_images.sh` was stopped after the classic
  Docker builder remained in workspace-context packaging for about four minutes.
  Two local BuildKit `--load` retries then failed before compilation while
  resolving `python:3.11-slim` from Docker Hub with `TLS handshake timeout`.
  No image was pushed.

3. Live API and browser:

- The running backend hot-reloaded the repository change.
- Authenticated live `GET http://127.0.0.1:8000/api/v1/workbench/summary`
  changed from HTTP 500 to HTTP 200 and returned 8 recent episodes plus 8 task
  queue entries.
- Preferred Chrome DevTools connection at `127.0.0.1:9222` timed out, so the
  repository harness recorded a Playwright fallback as `degraded`, not Chrome
  verification.
- Evidence run:
  `artifacts/runs/workbench-sort-memory-fix-20260716T1113Z/`.
- Playwright loaded the full workbench with the production-state cards, recent
  episodes, and task queue visible. Console had no errors or warnings.
- The final two `/api/v1/workbench/summary` responses were HTTP 200. Earlier
  `ERR_ABORTED` entries were requests cancelled during login navigation.
- After hot reload, authenticated live
  `GET /api/v1/episodes/49/timelines` returned HTTP 200 with Timeline `69`,
  version `39`.
- `GET /api/v1/timelines/69/resolved-videos` returned `ready=true`,
  `video_clip_count=36`, `missing_clip_count=0`, and
  `generating_clip_count=0`.
- The latest render remained render job `132`, status `succeeded`, output asset
  `574`.
- Preferred Chrome DevTools at `127.0.0.1:9222` timed out again. Playwright
  fallback evidence is stored at
  `artifacts/runs/episode49-timeline-video-track-20260716T1926Z/`.
- Playwright finished at
  `http://localhost:8090/episodes/49/workspace?tab=timeline&scriptId=30&clipId=video_scene_90_beat_3991_001`.
  The visible page showed the video main track, `36 个片段可渲染`,
  `成片 · 完成`, and `成片已就绪`; the earlier `缺视频` and `无视频轨`
  states were absent.

## Next Steps

- Repair the local Chrome DevTools endpoint if non-degraded Chrome evidence is
  required.
- Fix or isolate the backend quick-gate dependency resolver for Python 3.13.
- Isolate or repair the full-suite shared SQLite file fixtures before treating
  full `pytest` as a reliable local gate.
- Add a composite Timeline lookup index only if query-volume measurements justify
  a migration; the current primary-key projection removes the immediate failure.

## Linked Commits

- `a37b27e4` — `fix(backend): keep large timeline specs out of workbench sort`
- Episode Timeline list follow-up included in this commit.
