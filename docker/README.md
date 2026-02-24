# Dev stack in Docker

Local dev stack mirroring the ai-shifu workflow: build images from the repo, then run a compose file with bind mounts and hot reload.

## Lite quick start (SQLite + eager tasks)

Use this when you want a 5-10 minute startup path without MySQL/Redis/Celery worker:

1. `cd docker`
2. `cp .env.lite.example .env.lite`
3. `./dev_lite_in_docker.sh`

Lite stack services:

- `ai-video-nginx` / `ai-video-frontend` / `ai-video-backend`
- SQLite DB file: `ai-pic-backend/uploads/dev_lite.db`
- Celery runs in eager mode (`CELERY_TASK_ALWAYS_EAGER=true`)
- AI manager can be forced to mock (`AI_FORCE_MOCK=true`)
- SQLite migration fallback: `SQLITE_MIGRATION_FALLBACK_CREATE_ALL=true`
- Frontend API target defaults to `http://localhost:8089`

## Full quick start (MySQL + Redis + Celery)

1. `cd docker`
2. `cp .env.example .env` and fill any secrets (at minimum `SECRET_KEY`, optional AI keys). Default DB/Redis hosts match compose services.
3. `./dev_in_docker.sh`

Services & ports:

- Nginx entrypoint (dev): `http://localhost:8089` (routes `/api` → backend, `/` → frontend)
- Nginx entrypoint (prod): `http://localhost:8080` (see `docker-compose.prod.yml`)
- MySQL 8: container `ai-video-mysql` (no host port exposed; use `docker exec -it ai-video-mysql mysql -uroot -pai-video` if needed)
- Redis 7: internal only (service `ai-video-redis`)

The stack binds your local code into the containers for live reload:

- `../ai-pic-backend` → `/app/ai-pic-backend`
- `../ai-pic-frontend` → `/app/ai-pic-frontend`

MySQL/Redis data persist via Docker named volumes `mysql_data` and `redis_data`.

## Notes

- Backend uses `DATABASE_URL`/`REDIS_URL` from `.env`; defaults target the compose services.
- Frontend reads `NEXT_PUBLIC_API_URL` (often set to `http://host.docker.internal:8089` to hit Nginx from both browser and SSR); if that host is unavailable on your OS, set it to `http://localhost:8089`.
- Backend entrypoint waits for MySQL then runs `alembic upgrade head` automatically before starting uvicorn (see `backend-entrypoint.sh`).
- Image builds install backend requirements and frontend npm deps once; the mounted code updates without rebuilding.
