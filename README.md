# ai-video-studio

[中文](README_CN.md) | English

AI video production workflow platform for professional short drama teams.
Timeline-first, harness-tested, agent-assisted.

ai-video-studio is not a video generation model. It is an engineering workflow
system for AI short-drama, film, and TV production. It brings story, script,
audio, timeline, storyboard, assets, rendering, export, and test evidence into
one production chain.

The core idea is to help creative teams collaborate around a playable
`Timeline`, not around one-off model outputs. The current main chain is
`audio -> timeline -> clip -> render -> export`: `Timeline` is the single source
of truth (SSOT) for playable episode output, while Storyboard remains a visual
support view and compatibility surface.

## What It Does

- Manages production objects: virtual IP, stories, episodes, scripts, audio,
  Timeline, storyboard, and media assets.
- Turns AI outputs into traceable production assets instead of temporary prompts
  and files.
- Organizes clip editing, asset replacement, rendering, export, and quality
  evidence around Timeline.
- Supports reproducible engineering collaboration through harnesses, logs,
  browser evidence, and agent ledgers.

## Repository Layout

- `ai-pic-backend/`: FastAPI + SQLAlchemy + Alembic + Celery (MySQL/Redis)
- `ai-pic-frontend/`: Next.js 16 App Router + TypeScript + Tailwind
- `docker/`: local development and production Docker stacks with Nginx entrypoint
- `docs/`: design, API, and testing documentation index
- `tasks.md`: canonical product task board

## Quick Start: Lite Mode In 5-10 Minutes

Lite mode is the fastest local path. It uses SQLite, runs Celery tasks eagerly
in-process, and enables AI mock fallback by default. It does not require
MySQL, Redis, or a separate worker.

1. `cd docker`
2. `./init_env.sh lite`
3. `./dev_lite_in_docker.sh`

Open:

- Web app through Nginx: `http://localhost:8089`
- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

Key Lite defaults are stored in `docker/.env.lite`:

- `DATABASE_URL=sqlite:////app/ai-pic-backend/uploads/dev_lite.db`
- `CELERY_TASK_ALWAYS_EAGER=true`
- `AI_FORCE_MOCK=true`
- `SQLITE_MIGRATION_FALLBACK_CREATE_ALL=true`

## Full Docker Development Stack

Use this when you need MySQL, Redis, Celery worker, Celery beat, and real
provider integration.

1. `cd docker`
2. `./init_env.sh dev` and fill required values such as `DATABASE_URL`,
   `REDIS_URL`, `SECRET_KEY`, and AI keys as needed
3. `./dev_in_docker.sh`

Main containers:

- `ai-video-nginx` / `ai-video-frontend` / `ai-video-backend`
- `ai-video-celery-worker` / `ai-video-celery-beat`
- `ai-video-mysql` / `ai-video-redis`

Database migrations run automatically on backend container startup through
`docker/backend-entrypoint.sh`. If you update code without restarting the
backend and see errors such as `Unknown column ...`, run:

- `cd docker && ./migration_guard.sh check dev`
- `cd docker && ./migration_guard.sh fix dev`

## Local Development Without Docker

Backend:

```bash
cd ai-pic-backend
cp env.example .env

pip install -r requirements.txt -r requirements-test.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd ai-pic-frontend
npm install

export NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

## Harness Workflow

Default harness entrypoints:

- `scripts/harness/bootstrap_worktree.sh --mode lite`
- `python scripts/harness/doctor.py --run-id <run_id>`
- `python scripts/harness/browser_flow.py --scenario login_smoke --run-id <run_id>`
- `python scripts/harness/run_golden_path.py --scenario mock_smoke --run-id <run_id>`
- `python scripts/harness/query_logs.py --run-id <run_id>`
- `python scripts/harness/query_metrics.py --run-id <run_id>`
- `python scripts/harness/trace_run.py --run-id <run_id>`
- `python scripts/harness/trace_task.py --task-id <task_id>`
- `python scripts/harness/score_quality.py --run-id <run_id> --write-quality-score`

Harness evidence is written to `artifacts/runs/<run_id>/`, including manifests,
summaries, console and network captures, DOM snapshots, screenshots, and
scenario-specific browser evidence. Contract audit output is written to
`artifacts/repo_audit/latest/`.

## Prompt Templates And Story Formats

The system supports format-aware prompt routing:

- `story_format`: `short_drama` by default, plus `tv_series` and `film`
- The frontend story generation form exposes a format selector
- Prompt templates live under `ai-pic-backend/app/prompts/templates/`

Naming convention:

- Base templates: `story_outline`, `system_prompt_story`,
  `system_prompt_script`, `episode_generation`, `script_scenes`
- Variants: `<base>_tv_series`, `<base>_film`

Resolver implementation:

- `ai-pic-backend/app/prompts/template_resolver.py`
- `ai-pic-backend/app/prompts/manager.py`

## Export Zhihu-Style Novels

- Entry: story detail page, `Export Zhihu-style novel`
- Flow: async task plus Celery worker; the page polls progress and downloads a
  `.txt` file when complete
- Backend endpoints:
  - `POST /api/v1/stories/business/{story_business_id}/novel/generate-async`
  - `GET /api/v1/stories/novel/tasks/{task_id}/download`
- Prompt templates: `system_prompt_novel_zhihu`,
  `story_novel_zhihu_plan`, `story_novel_zhihu_chapter`
- Output path: `uploads/exports/novels/`
- Database table: `story_novel_exports`

## Agent State Graphs

LangGraph can export state machines to Mermaid and PNG. This repository only
snapshots paths that actually build a `StateGraph`. `StoryLangGraphAgent` and
`EpisodeLangGraphAgent` are structured repair loops; their names remain for
compatibility and are not listed as LangGraph diagrams.

- Generate diagrams: `python scripts/generate_agent_graphs.py`
- Output directory: `docs/agent_graphs/`

Available graph snapshots include:

- `ScriptLangGraphAgent`: script generation
- `StoryboardPipeline`: explicit storyboard pipeline
- `StoryboardReActReasoner`: storyboard planning, critique, and generation
- `TimelineLangGraphAgent`: legacy dialogue rhythm and gap timing
- `DurationOrchestratorAgent`: experimental duration control loop

## Validation

Common validation commands:

```bash
cd ai-pic-backend && pytest
cd ai-pic-frontend && npm run lint
python scripts/check_repo_docs.py
python scripts/check_repo_contracts.py --mode audit
```

## Documentation

- Docs index: `docs/README.md`
- Architecture: `ARCHITECTURE.md`
- Frontend rules: `FRONTEND.md`
- Reliability and tracing: `RELIABILITY.md`
- Security: `SECURITY.md`
- Quality score: `QUALITY_SCORE.md`
- Docker stack: `docker/README.md`
- Backend: `ai-pic-backend/README.md`
- Frontend: `ai-pic-frontend/README.md`

## Troubleshooting

- Stories pages are empty or fail to load, and backend logs show
  `Unknown column 'stories.story_format'`: run `alembic upgrade head`, or use
  `docker exec ai-video-backend ...` inside Docker.
- Novel export tasks stay `pending` or `processing`: confirm Redis and
  `ai-video-celery-worker` are running, then inspect worker logs.
- Nginx occasionally returns `502 Bad Gateway` after container IP changes:
  restart it with `docker restart ai-video-nginx`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
