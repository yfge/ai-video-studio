# Architecture

ai-video-studio adopts a harness-first workflow around two primary apps:

- `ai-pic-backend/`: FastAPI, SQLAlchemy, Alembic, Celery, provider integrations.
- `ai-pic-frontend/`: Next.js App Router, typed API client, operator-facing workflows.

## System of Record

- `tasks.md` is the business roadmap and product task board.
- `AGENTS.md` is the workflow entrypoint for coding agents.
- This file records structural rules and known choke points.
- `RELIABILITY.md` records runtime, logging, and browser-evidence rules.

## Layering

- Backend direction: `api -> services -> repositories -> models`.
- Frontend direction: `app -> feature hooks/components -> shared ui -> api client`.
- `scripts/` hosts repo automation, harness CLIs, and checks; it is not a dumping ground for app logic.

## Known Choke Points

- `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`
- `ai-pic-backend/app/services/dialogue_audio_service.py`
- `ai-pic-backend/app/services/ai_service_manager.py`

These files are tolerated as baseline debt. New work must not add fresh dependencies on them unless the file itself is being reduced.

## Harness Requirements

- Every worktree should be bootstrap-able with `scripts/harness/bootstrap_worktree.sh`.
- Every meaningful validation should emit artifacts under `artifacts/runs/<run_id>/`.
- Repo checks live in `scripts/check_repo_docs.py` and `scripts/check_repo_contracts.py`.
