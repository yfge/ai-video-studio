# Testing Policy

This document defines the minimum validation gates for repository changes.

## Core Rule

Choose the smallest validation set that matches the risk. Do not skip the baseline gate for the affected surface.

## Repo-Level Checks

- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`

Use audit mode when updating quality snapshots or debt reports:

- `python scripts/check_repo_contracts.py --mode audit`

## Backend Validation

- Narrow service, validator, repository, or prompt change:
  - `cd ai-pic-backend && python run_tests.py quick`
- Clear nearby test coverage:
  - `cd ai-pic-backend && pytest <path-or-node> -v`
- API, auth, model, migration, background task, or shared contract change:
  - `cd ai-pic-backend && pytest`

## Frontend Validation

- Always:
  - `cd ai-pic-frontend && npm run lint`
- Add for behavior or state changes:
  - `cd ai-pic-frontend && npm run test`
- Add for route, layout, auth, config, or hydration-sensitive changes:
  - `cd ai-pic-frontend && npm run build`

## Browser Validation

Run a real browser path for:

- login flows
- frontend/backend integration changes
- AI or media generation flows
- user-visible workflow changes

Preferred order:

1. Chrome DevTools
2. Playwright
3. Selenium

Record the actual engine used. Do not label a fallback run as Chrome verification.

## Harness Validation

Harness runs should write artifacts under `artifacts/runs/<run_id>/`.

Core commands:

- `scripts/harness/bootstrap_worktree.sh --mode lite`
- `python scripts/harness/doctor.py --run-id <run_id>`
- `python scripts/harness/browser_flow.py --scenario <name> --run-id <run_id>`
- `python scripts/harness/run_golden_path.py --scenario <name> --run-id <run_id>`
- `python scripts/harness/trace_run.py --run-id <run_id>`

## Pre-Commit And Pre-Push Expectations

- `pre-commit` hooks are part of the contract, not optional hygiene.
- Before commit, run `./docker/build_prod_images.sh`.
- Document any validation omission or downgrade in the matching `agent_chats` entry.
