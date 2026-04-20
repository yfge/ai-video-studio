# Agents Guidance for ai-video-studio

This file is the lightweight entrypoint for every coding agent working in this repository. Treat it as the table of contents, not the encyclopedia. Detailed policy lives in the linked docs under `docs/`.

## Instruction Order

- Follow: system / developer -> user -> `AGENTS.md` -> linked repository docs.
- Keep `CLAUDE.md` and `GEMINI.md` as exact mirrors or symlinks to this file.
- Keep real rules in the repository. Do not treat chat history, ad-hoc notes, or personal memory as source of truth.

## Repository Mission

ai-video-studio is an AI production platform with:

- `ai-pic-backend/`: FastAPI, SQLAlchemy, Alembic, Celery, provider integrations.
- `ai-pic-frontend/`: Next.js 16 App Router operator workflows.
- `scripts/`: repository automation, harness CLIs, and enforcement checks.
- `tasks.md`: the canonical product task board. Do not create or revive `task.md`.

## Agent System Of Record

Start here, then read only the docs needed for the task:

- [ARCHITECTURE.md](/Users/geyunfei/dev/yfge/ai-video-studio/ARCHITECTURE.md): system layout, dependency direction, choke points.
- [FRONTEND.md](/Users/geyunfei/dev/yfge/ai-video-studio/FRONTEND.md): frontend structure rules and harness notes.
- [RELIABILITY.md](/Users/geyunfei/dev/yfge/ai-video-studio/RELIABILITY.md): harness runtime modes, browser evidence, trace policy.
- [SECURITY.md](/Users/geyunfei/dev/yfge/ai-video-studio/SECURITY.md): security and secret-handling constraints.
- [docs/README.md](/Users/geyunfei/dev/yfge/ai-video-studio/docs/README.md): full docs index.
- [docs/architecture/contracts.md](/Users/geyunfei/dev/yfge/ai-video-studio/docs/architecture/contracts.md): repo contracts, audit outputs, choke-point policy.
- [docs/architecture/file-size-limits.md](/Users/geyunfei/dev/yfge/ai-video-studio/docs/architecture/file-size-limits.md): file-size and layering limits.
- [docs/architecture/testing-policy.md](/Users/geyunfei/dev/yfge/ai-video-studio/docs/architecture/testing-policy.md): validation matrix and minimum gates.
- [docs/architecture/agent-workflow.md](/Users/geyunfei/dev/yfge/ai-video-studio/docs/architecture/agent-workflow.md): ledger, commit discipline, browser validation recording.
- [docs/generated/db-schema.md](/Users/geyunfei/dev/yfge/ai-video-studio/docs/generated/db-schema.md): current schema snapshot.
- `docs/exec-plans/active/` and `docs/exec-plans/completed/`: tracked execution plans.

## Working Rules

- Use repository-local, versioned artifacts as the source of truth.
- Keep new code aligned with the existing domain layering:
  - backend: `api -> services -> repositories -> models`
  - frontend: `app -> feature hooks/components -> shared ui -> api client`
- Do not add new dependencies on the known choke points listed in `ARCHITECTURE.md`.
- Do not add new direct SQLAlchemy `.query(...)` access outside repositories.
- When a rule belongs in automation, encode it in code or docs instead of repeating it in prompts.

## Validation Baseline

- Repo docs and mirrors:
  - `python scripts/check_repo_docs.py`
- Repo contracts:
  - `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - `python scripts/check_repo_contracts.py --mode audit`
- Backend:
  - narrow/shared changes: `cd ai-pic-backend && python run_tests.py quick`
  - API/auth/model/migration changes: `cd ai-pic-backend && pytest`
- Frontend:
  - always: `cd ai-pic-frontend && npm run lint`
  - add `npm run test` for behavior/state/API-client changes
  - add `npm run build` for route, layout, auth, config, or hydration-sensitive changes
- Harness:
  - `scripts/harness/bootstrap_worktree.sh --mode lite`
  - `python scripts/harness/doctor.py --run-id <run_id>`
  - `python scripts/harness/browser_flow.py --scenario <name> --run-id <run_id>`
  - `python scripts/harness/run_golden_path.py --scenario <name> --run-id <run_id>`
  - `python scripts/harness/trace_run.py --run-id <run_id>`

## Browser Evidence Policy

- For login, frontend/backend integration, AI calls, image/video flows, and other user-visible functional changes, run a real browser validation path.
- Preferred engine is Chrome DevTools. Fallback to Playwright or Selenium only when Chrome transport fails, and record the fallback explicitly.
- Store evidence under `artifacts/runs/<run_id>/`.
- Do not claim Chrome verification when the run actually used a fallback engine.
- Current test account for real-browser validation:
  - username: `geyunfei`
  - password: `Gyf@845261`

## Delivery Discipline

- Keep changes atomic and traceable.
- Pair every code change under `ai-pic-backend/`, `ai-pic-frontend/`, `scripts/`, or this file with a matching `agent_chats` ledger entry in the same commit.
- Ledger path format: `agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-topic.md`
- Required ledger sections, in order:
  - `## User Prompt`
  - `## Goals`
  - `## Changes`
  - `## Validation`
  - `## Next Steps`
  - `## Linked Commits`
- Before commit, ensure:
  - relevant tests pass
  - `pre-commit run --all-files` is clean or any skip is documented
  - `./docker/build_prod_images.sh` succeeds
- Use Conventional Commit subjects.

## Quality Bar

- Respect the file-size and structure limits in `docs/architecture/file-size-limits.md`.
- Favor thin controllers, focused services, explicit repositories, and colocated frontend feature state.
- New work must reduce or isolate debt; it must not widen the historical hotspots.
- When logs, requests, or browser evidence contradict your assumption, stop asserting and reproduce the issue with real evidence before concluding.

## Review Mindset

- Prioritize regressions, broken flows, structural drift, and missing validation.
- Record decisive commands, browser paths, console output, and network evidence in `agent_chats`.
- Summarize remaining risks or TODOs when handing work back.
