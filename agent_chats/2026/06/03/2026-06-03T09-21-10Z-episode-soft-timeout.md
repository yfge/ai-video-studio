---
id: 2026-06-03T09-21-10Z-episode-soft-timeout
date: "2026-06-03T09:21:10Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, episode-generation, celery]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/__init__.py
  - ai-pic-backend/app/repositories/episode_repository.py
  - ai-pic-backend/app/services/episode/async_generation_task.py
  - ai-pic-backend/app/services/episode/async_generation_task_helpers.py
  - ai-pic-backend/app/services/episode/episode_generation_result_processor.py
  - ai-pic-backend/app/services/episode/episode_stream_persistence.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/fixtures/mock_ai_service.py
  - ai-pic-backend/tests/unit/services/episode/test_async_generation_task_helpers.py
  - ai-pic-backend/tests/unit/test_episode_async_incremental_persistence.py
summary: "Keep streamed episode plans through Celery soft timeouts and normalize async marketing payloads"
---

## User Prompt

生成剧集 - 故事48
失败
进度：SoftTimeLimitExceeded()

Episode plan for story 48

生成剧集 - 故事48
失败
进度：AI剧集生成失败

Episode plan for story 48

## Goals

- Diagnose why async episode generation for Story 48 failed with `SoftTimeLimitExceeded()`.
- Diagnose why the follow-up Story 48 run failed immediately with `AI剧集生成失败`.
- Make long episode-plan generation more resilient without broad unrelated changes.
- Preserve validated per-episode outputs when the Celery worker hits a soft timeout.
- Keep async episode prompt inputs JSON-serializable after request validation.

## Changes

- Added an `on_episode` callback in async episode generation so each LangGraph-generated episode is validated, normalized, and persisted as soon as it is emitted.
- Refactored async episode task orchestration out of the oversized FastAPI endpoint into focused service modules.
- Refactored async episode persistence into a shared service helper used by both streamed callbacks and final fallback processing.
- Preserved streamed episode rows on `SoftTimeLimitExceeded`, while keeping the existing cleanup behavior for non-timeout failures.
- Added an episode-specific Celery timeout for `tasks.episode_generate`: 7200s soft limit and 7500s hard limit.
- Added unit coverage for task time-limit configuration and preserving streamed episodes on soft timeout.
- Updated backend AI-service test fixture patching to target the new async task service binding.
- Found the second failure in worker logs: `Failed to render template episode_step_outline: Object of type HookPlan is not JSON serializable`.
- Normalized async episode marketing overrides from Pydantic request models to plain `dict`/`list` payloads before prompt rendering.
- Added unit coverage proving `build_marketing_overrides()` returns JSON-serializable `hook_plan` and `ad_snippets` payloads after `EpisodeGenerationRequest.model_validate(...)`.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_episode_async_incremental_persistence.py -q` -> passed, 2 tests.
- `cd ai-pic-backend && pytest tests/unit/test_episode_agent_callbacks.py tests/unit/test_episode_step_outline_light.py tests/api/test_episode_outline_persistence.py tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run -q` -> passed, 7 tests.
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed for changed episode async task, service, repository, test fixture, unit test, task worker, and ledger files.
- `python scripts/check_repo_docs.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_episode_async_incremental_persistence.py tests/unit/test_episode_agent_callbacks.py tests/unit/test_episode_step_outline_light.py tests/api/test_episode_outline_persistence.py tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run -q` -> passed, 9 tests.
- `cd ai-pic-backend && pytest tests/unit -q` -> passed, 1816 tests, 56 skipped.
- `cd ai-pic-backend && pytest` -> interrupted after the full suite hung in Selenium manager while setting up Chrome during early API tests; no failure from the episode task change was observed before the hang.
- `cd ai-pic-backend && pytest tests/unit/services/episode/test_async_generation_task_helpers.py -q` -> failed before the fix because `hook_plan` remained a `HookPlan` object; passed after the fix, 1 test.
- `cd ai-pic-backend && pytest tests/unit/services/episode/test_async_generation_task_helpers.py tests/unit/test_episode_async_incremental_persistence.py tests/unit/test_episode_agent_callbacks.py tests/unit/test_episode_step_outline_light.py tests/api/test_episode_outline_persistence.py tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run -q` -> passed, 10 tests.
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed for changed episode async task, helper, service, repository, test fixture, unit tests, task worker, and ledger files.
- `python scripts/check_repo_docs.py` -> passed.
- `cd ai-pic-backend && python run_tests.py quick` -> did not reach tests; dependency installation failed under Python 3.13 because `langchain-core==0.2.43` requires `pydantic>=2.7.4` while the repo pins `pydantic==2.5.0`.
- `cd ai-pic-backend && pytest tests/unit -q` -> passed, 1817 tests, 56 skipped.
- `docker compose -f docker/docker-compose.dev.yml restart ai-video-celery-worker` -> restarted the dev Celery worker.
- `docker logs ai-video-celery-worker --tail 50` -> worker registered `tasks.episode_generate` and reached `celery@... ready`.
- `docker exec ai-video-celery-worker python -c '...'` -> printed `7200 7500 dict dict`, confirming the worker loaded the episode timeout settings and JSON-serializable marketing payload conversion.

## Next Steps

- Re-run Story 48 episode generation after deploying/restarting the Celery worker so the new task options and payload normalization take effect.
- Investigate the full-suite Selenium manager hang separately if full backend `pytest` is required before merge.
- Investigate the `run_tests.py quick` dependency resolver conflict separately if that harness path must be used on Python 3.13.

## Linked Commits

- Pending.
