## User Prompt

现在一个剧集生成要跑好久，看一下docker 是不是有一些限制做的过分了？

## Goals

- Check whether Docker or compose resource limits are throttling episode generation.
- Inspect the current worker/runtime evidence before changing configuration.
- Fix the concrete storage failure found during diagnosis.

## Changes

- Confirmed Docker Desktop exposes 12 CPUs and about 31GB memory to containers.
- Confirmed `ai-video-celery-worker`, backend, MySQL, Redis, frontend, and nginx have no per-container CPU, memory, pids, or ulimit caps.
- Found current worker concurrency is 12 prefork processes, so the worker is not constrained to a single process.
- Found recent story 12 episode generation tasks were long-running production jobs for 10 three-minute episodes with `deepseek:deepseek-v4-pro`.
- Found worker logs showing MySQL `Data too long for column 'generation_prompt'` while persisting a generated episode.
- Expanded `Episode.generation_prompt` to MySQL `LONGTEXT`.
- Added Alembic migration `d4e5f6a7b8c9_expand_episode_generation_prompt_longtext.py`.
- Added a model schema regression test for the MySQL `LONGTEXT` mapping.
- Applied the migration to the current Docker MySQL database.

## Validation

1. Runtime diagnosis:

- `docker info --format '{{json .}}'` -> Docker Desktop runtime reports `NCPU=12` and `MemTotal=33337647104`.
- `docker inspect ai-video-celery-worker ai-video-backend ai-video-celery-beat ai-video-mysql ai-video-redis ai-video-frontend ai-video-nginx` -> all relevant containers report `Memory=0`, `NanoCpus=0`, `CpuQuota=0`, and `PidsLimit=null`.
- `docker stats --no-stream ...` -> worker used about 1.16GB-1.27GB of a 31.05GB limit; CPU was low to moderate during inspection.
- `docker exec ai-video-celery-worker celery -A app.core.celery_app.celery_app inspect stats --timeout=5` -> worker pool `max-concurrency=12`, `prefetch_count=48`.
- `docker exec ai-video-mysql ... SELECT ... FROM tasks WHERE id IN (6231,6230,6229,6228)` -> task 6230 ran 7216 seconds and failed; task 6231 was still processing past 7200 seconds.
- `docker logs ai-video-celery-worker --since '2026-06-23T10:25:00' --tail 2000 ...` -> found `Data too long for column 'generation_prompt'` during episode persistence.

2. Code checks:

- `cd ai-pic-backend && pytest tests/unit/models/test_episode_generation_prompt_schema.py -q` -> failed before the fix because `generation_prompt` mapped to MySQL `Text()`.
- `cd ai-pic-backend && pytest tests/unit/models/test_episode_generation_prompt_schema.py -q` -> passed after the fix.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/models/script.py ai-pic-backend/alembic/versions/d4e5f6a7b8c9_expand_episode_generation_prompt_longtext.py ai-pic-backend/tests/unit/models/test_episode_generation_prompt_schema.py` -> passed.
- `python scripts/check_repo_contracts.py --mode audit` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `git diff --check` -> passed.
- `cd ai-pic-backend && pytest` -> interrupted after 163 seconds because the suite stopped making progress; partial result was 8 passed, 2 skipped, 391 warnings, then `KeyboardInterrupt`.

3. Current Docker DB migration:

- `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && alembic upgrade head'` -> ran `c5e6f7a8b9c0 -> d4e5f6a7b8c9`.
- `docker exec ai-video-mysql ... SHOW FULL COLUMNS FROM episodes LIKE 'generation_prompt'` -> column is now `longtext`.

## Next Steps

- Do not treat Docker resource limits as the primary bottleneck for this case.
- Consider explicitly cancelling stale active Celery tasks 6230 and 6231 if the operator wants to clear the current queue.
- Consider a separate follow-up to split 10-episode production generation into smaller resumable jobs or relax Celery episode time limits with stronger partial-result semantics.

## Linked Commits

- Pending.
