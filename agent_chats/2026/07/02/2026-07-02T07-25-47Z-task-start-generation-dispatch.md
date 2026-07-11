## User Prompt

修复生成链路检查中发现的任务重启分发问题。

## Goals

- 修复 Timeline clip video rework 的 `VIDEO_GENERATION` 任务手动重启错派到 storyboard video worker 的问题。
- 修复 deprecated `TIMELINE_GENERATION` 任务无法从任务页手动重启的问题。
- 保持主生成链路和既有 storyboard video 任务行为不变。

## Changes

- 在 `/tasks/{task_id}/start` 的 Celery dispatch 边界中，按任务参数区分 Timeline clip rework video 任务并派发到 `timeline_clip_rework_video_generate_task`。
- 为 `TaskType.TIMELINE_GENERATION` 补回 `script_audio_timeline_generate_task` 手动重启映射。
- 新增任务分发回归测试覆盖两个重启路径。

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/test_task_start_dispatch.py -q` -> failed before fix: Timeline rework video task dispatched to storyboard worker; `TIMELINE_GENERATION` returned unsupported.
- `cd ai-pic-backend && rm -f test.db && pytest tests/test_task_start_dispatch.py tests/test_tasks_minimal.py tests/test_task_cancel_api.py tests/unit/services/video/test_timeline_clip_video_rework_submission.py tests/test_timeline_clip_video_rework_api.py tests/test_timeline_clip_tasks_api.py -q` -> passed, 16 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_agent_chats.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/tasks.py ai-pic-backend/app/repositories/task_repository.py ai-pic-backend/app/models/script.py ai-pic-backend/alembic/versions/d4e5f6a7b8c9_expand_episode_generation_prompt_longtext.py ai-pic-backend/tests/test_task_start_dispatch.py ai-pic-backend/tests/unit/models/test_episode_generation_prompt_schema.py agent_chats/2026/06/23/2026-06-23T12-38-13Z-episode-generation-docker-limit-diagnosis.md agent_chats/2026/07/02/2026-07-02T07-25-47Z-task-start-generation-dispatch.md` -> passed.

2. Browser or MCP validation:

- Not run. This change is task dispatch routing only and does not alter frontend UI or provider request payloads.

3. Conflict signals and corrections:

- Initial parallel pytest commands hit SQLite `test.db` contention (`attempt to write a readonly database`); reran the same tests serially after removing the generated test DB.

## Next Steps

- 无。

## Linked Commits

- Pending.
