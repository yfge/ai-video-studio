---
id: 2026-01-28T04-23-28Z-task-agent-run-backfill
date: 2026-01-28T04:23:28Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tasks, migration]
related_paths:
  - ai-pic-backend/alembic/versions/8848b61e51a8_expand_tasks_parameters_longtext.py
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/app/services/task_agent_run/persistence.py
  - tasks.md
summary: "Expand tasks.parameters to LONGTEXT and complete full agent_run backfill"
---

## User Prompt

- "全量回填 吧现在几乎没有什么数据"
- "把 P0 的都处理"
- "继续完成 P0 任务"

## Goals

- Remove MySQL TEXT size limit blocker for task audit backfill.
- Backfill `parameters.agent_run` for historical tasks (including FAILED/CANCELLED) so /tasks is auditable.
- Verify in Chrome that /tasks shows agent_run details.

## Changes

- Added Alembic migration to expand `tasks.parameters` from TEXT to LONGTEXT on MySQL.
- Updated Task model column to use MySQL LONGTEXT variant.
- Ensured terminal tasks always receive minimal agent_run context during persistence (completed now also enriched).
- Ran full historical backfill for `parameters.agent_run` and confirmed zero remaining candidates.
- Marked the production backfill task as complete in `tasks.md` and noted LONGTEXT expansion.

## Validation

- DB migration: `docker exec -i ai-video-backend alembic upgrade head`
- Backfill run: `docker exec -i ai-video-backend python scripts/backfill_task_agent_runs.py --apply --max-updates 20000`
- Backfill verification: `docker exec -i ai-video-backend python scripts/backfill_task_agent_runs.py --show-samples 3` (candidates=0)
- Pytest (fails): `docker exec -i ai-video-backend pytest --maxfail=1` → `tests/test_api.py::TestVirtualIPAPI::test_create_virtual_ip` expects 201 but got 200
- Build: `./docker/build_prod_images.sh`
- Chrome E2E: login `geyunfei` → `/tasks` → expand task details (e.g., storyboard_image_generation and script_generation) to confirm `parameters.agent_run` is present

## Next Steps

- Investigate and fix failing test `tests/test_api.py::TestVirtualIPAPI::test_create_virtual_ip` (HTTP 200 vs 201).
- Proceed to remaining P1 items once backend tests are green.

## Linked Commits

- TBD
