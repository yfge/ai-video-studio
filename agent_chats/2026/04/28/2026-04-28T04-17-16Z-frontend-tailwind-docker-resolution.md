## User Prompt

User reported the Docker frontend container failing with `Error: Can't resolve 'tailwindcss' in '/app'`.

## Goals

- Diagnose why Tailwind resolves locally but fails inside the frontend dev container.
- Fix the container dependency layout without changing frontend runtime behavior.
- Validate the frontend and Docker resolution path.

## Changes

- Updated `docker/Dockerfile.frontend.dev` to expose `/app/ai-pic-frontend/node_modules` at `/app/node_modules` with a symlink, so resolvers that start from `/app` can find Tailwind while the app still runs from `/app/ai-pic-frontend`.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npm run lint` -> passed with 19 existing warnings and 0 errors.
- `cd ai-pic-frontend && npm run build` -> passed; Next.js 16.1.3 compiled all routes successfully.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff docker/Dockerfile.frontend.dev agent_chats/2026/04/28/2026-04-28T04-17-16Z-frontend-tailwind-docker-resolution.md` -> passed; no diff-sensitive rules applied to these paths.
- `python scripts/check_agent_chats.py` -> passed.

2. Docker validation:

- Before the fix, `docker compose --env-file .env.lite -f docker-compose.lite.yml run --rm --no-deps ai-video-frontend node -e "require.resolve('tailwindcss', { paths: ['/app'] })"` failed with `Cannot find module 'tailwindcss'`; `/app/node_modules` did not exist.
- After the fix, `docker compose --env-file .env.lite -f docker-compose.lite.yml build ai-video-frontend` -> passed and created the symlink layer.
- After the fix, `docker compose --env-file .env.lite -f docker-compose.lite.yml run --rm --no-deps ai-video-frontend node -e "console.log(require.resolve('tailwindcss', { paths: ['/app'] }))"` -> passed and resolved to `/app/ai-pic-frontend/node_modules/tailwindcss/dist/lib.js`.
- Runtime smoke: `docker compose --env-file .env.lite -f docker-compose.lite.yml run --rm --no-deps -p 13123:3000 ai-video-frontend`, then `curl -I --fail http://localhost:13123/login` -> `HTTP/1.1 200 OK`; dev server log showed `HEAD /login 200` after compilation.

## Next Steps

- Rebuild/recreate any already-running frontend dev container so it uses the updated image layer.

## Linked Commits

- This commit: `fix: expose frontend dev node modules`
