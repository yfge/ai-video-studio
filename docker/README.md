# Dev stack in Docker

Local dev stack mirroring the ai-shifu workflow: build images from the repo, then run a compose file with bind mounts and hot reload.

## Quick start
1. `cd docker`
2. `cp .env.example .env` and fill any secrets (at minimum `SECRET_KEY`, optional AI keys). Default DB/Redis hosts match compose services.
3. `./dev_in_docker.sh`

Services & ports:
- Backend (FastAPI + Uvicorn): `http://localhost:8000`
- Frontend (Next.js dev server): `http://localhost:3000`
- MySQL 8: host `localhost`, port `13306`, db `ai_video_studio`, user `root`, password `ai-video`
- Redis 7: host `localhost`, port `16379`

The stack binds your local code into the containers for live reload:
- `../ai-pic-backend` → `/app/ai-pic-backend`
- `../ai-pic-frontend` → `/app/ai-pic-frontend`

MySQL/Redis data persist via Docker named volumes `mysql_data` and `redis_data`.

## Notes
- Backend uses `DATABASE_URL`/`REDIS_URL` from `.env`; defaults target the compose services.
- Frontend reads `NEXT_PUBLIC_API_URL` (defaults to backend exposed at 8000).
- Image builds install backend requirements and frontend npm deps once; the mounted code updates without rebuilding.
