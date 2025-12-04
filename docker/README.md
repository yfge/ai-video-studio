# Dev stack in Docker

Local dev stack mirroring the ai-shifu workflow: build images from the repo, then run a compose file with bind mounts and hot reload.

## Quick start
1. `cd docker`
2. `cp .env.example .env` and fill any secrets (at minimum `SECRET_KEY`, optional AI keys). Default DB/Redis hosts match compose services.
3. `./dev_in_docker.sh`

Services & ports:
- Nginx entrypoint: `http://localhost:8080` (routes `/api` → backend, `/` → frontend)
- MySQL 8: container `ai-video-mysql` (no host port exposed; use `docker exec` or add a temporary port mapping if needed)
- Redis 7: internal only (service `ai-video-redis`)

The stack binds your local code into the containers for live reload:
- `../ai-pic-backend` → `/app/ai-pic-backend`
- `../ai-pic-frontend` → `/app/ai-pic-frontend`

MySQL/Redis data persist via Docker named volumes `mysql_data` and `redis_data`.

## Notes
- Backend uses `DATABASE_URL`/`REDIS_URL` from `.env`; defaults target the compose services.
- Frontend reads `NEXT_PUBLIC_API_URL` (defaults to `http://host.docker.internal:8080` to hit Nginx from both browser and SSR); if that host is unavailable on your OS, set it to `http://localhost:8080`.
- Image builds install backend requirements and frontend npm deps once; the mounted code updates without rebuilding.
