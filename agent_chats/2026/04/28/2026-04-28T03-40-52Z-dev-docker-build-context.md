---
id: 2026-04-28T03-40-52Z-dev-docker-build-context
date: "2026-04-28T03:40:52Z"
participants: [human, codex]
models: [gpt-5]
tags: [docker, dev-env]
related_paths:
  - docker/docker-compose.dev.yml
  - docker/Dockerfile.backend.dev
  - docker/Dockerfile.frontend.dev
summary: "Aligned full dev Docker build contexts with service source directories so dev images can copy backend requirements and frontend package manifests."
---

## User Prompt

`./dev_in_docker.sh` failed while building dev images because `Dockerfile.backend.dev` could not copy `requirements.txt` from the build context.

## Goals

- Restore the full dev Docker stack build.
- Keep full dev compose behavior aligned with lite compose.
- Preserve bind-mounted hot reload behavior for backend and frontend services.

## Changes

- Changed full dev compose build contexts from the repository root to `../ai-pic-backend` and `../ai-pic-frontend`, matching the dev Dockerfiles' expected `COPY` paths.
- Updated backend and frontend dev Dockerfiles to use runtime-aligned workdirs under `/app/ai-pic-backend` and `/app/ai-pic-frontend`.
- Kept runtime bind mounts and commands unchanged.

## Validation

- `cd docker && docker compose -f docker-compose.dev.yml config`
  - Passed; full dev compose resolves backend and frontend build contexts to the expected source directories.
- `cd docker && docker compose -f docker-compose.dev.yml build`
  - Passed; built `ai-video-backend`, `ai-video-celery-worker`, `ai-video-celery-beat`, and `ai-video-frontend`.
- `cd docker && docker compose --env-file .env.lite -f docker-compose.lite.yml build`
  - Passed; shared dev Dockerfiles still build for the lite stack.
- `python scripts/check_repo_contracts.py --mode diff docker/docker-compose.dev.yml docker/Dockerfile.backend.dev docker/Dockerfile.frontend.dev agent_chats/2026/04/28/2026-04-28T03-40-52Z-dev-docker-build-context.md`
  - Passed; no changed-file diff rules applied to these files.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python - <<'PY' ... validate_agent_file(...)`
  - Passed; ledger frontmatter and required sections are valid.
- `BUILD_PUSH=false ./docker/build_prod_images.sh`
  - Passed; backend and frontend production images built locally without pushing.
- `pre-commit run --all-files`
  - Failed on existing repo-wide lint/format drift outside this Docker fix. Several format hooks rewrote unrelated files; those unstaged hook rewrites were reverted to keep this commit scoped. The backend quick gate and frontend lint subhooks completed successfully.
- `pre-commit run`
  - Passed for staged files.

## Next Steps

- If startup proceeds past build, verify migrations and frontend dev server logs.

## Linked Commits

- Pending.
