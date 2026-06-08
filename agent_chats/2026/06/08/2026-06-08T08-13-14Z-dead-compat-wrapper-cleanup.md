---
id: 2026-06-08T08-13-14Z-dead-compat-wrapper-cleanup
date: "2026-06-08T08:13:14Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - backend
  - scripts
  - dead-code
related_paths:
  - ai-pic-backend/app/services/task_agent_run_persistence.py
  - ai-pic-backend/app/services/audio/voice_catalog.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/task_worker_assets.py
  - ai-pic-backend/app/services/task_worker_storyboard_media.py
  - ai-pic-backend/app/services/task_worker_timeline_rework.py
  - ai-pic-backend/app/services/video/video_task_polling_parent_task.py
  - ai-pic-backend/scripts/backfill_task_agent_runs.py
  - ai-pic-backend/tests/unit/services/audio/test_voice_catalog.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_assets.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_extra.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_failed.py
  - scripts/contract_audit_core.py
  - tests/harness/test_repo_contracts.py
summary: Removed obsolete compatibility wrapper modules and stale contract-audit exemptions after migrating internal imports to canonical modules.
---

## User Prompt

Continue goal: 清理项目的死代码，直到没有

## Goals

- Keep reducing old dead code using current repository evidence.
- Remove compatibility wrapper modules only when project-internal imports can be migrated to canonical modules.
- Keep unrelated episode/rework frontend worktree changes out of this batch.

## Changes

- Removed stale `scripts_legacy.py` oversized, route-handler, and direct-query contract exemptions after the current file no longer matched those historical debt baselines.
- Updated the contract harness test to use a generic baseline-debt fixture path instead of codifying `scripts_legacy.py` as the example.
- Migrated internal `persist_task_agent_run` imports to the canonical `app.services.task_agent_run` package export.
- Deleted obsolete `app.services.task_agent_run_persistence` after repository search showed no remaining internal references.
- Deleted obsolete `app.services.audio.voice_catalog`; runtime code already uses `app.services.voice_catalog`, and the old wrapper was only referenced by its own compatibility test.
- Split task-agent-run persistence tests by domain so touched files stay within repository size contracts.
- Moved parent video task lookup to `TaskRepository.get_by_id()` to avoid preserving direct SQLAlchemy access in a touched service helper.

## Validation

- Passed: `ai-pic-backend/.venv/bin/python -m pyflakes ai-pic-backend/app ai-pic-backend/tests ai-pic-backend/scripts scripts`.
- Passed: `ai-pic-backend/.venv/bin/python -m compileall -q ai-pic-backend/app ai-pic-backend/scripts scripts tests/harness/test_repo_contracts.py`.
- Passed: `python scripts/check_repo_contracts.py --mode audit`.
- Passed: `python scripts/check_repo_contracts.py --mode diff <changed backend/scripts/harness files>`.
- Passed: `ai-pic-backend/.venv/bin/python -m pytest tests/harness/test_repo_contracts.py`.
- Passed: `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/services/audio/test_voice_catalog.py ai-pic-backend/tests/unit/services/test_task_agent_run_persistence.py ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_assets.py ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_extra.py ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_failed.py` (`44 passed`).
- Passed: `cd ai-pic-frontend && npm exec -- tsc --noEmit --noUnusedLocals --noUnusedParameters --pretty false`.
- Passed: `cd ai-pic-frontend && npm run lint` (0 errors, 4 existing warnings).
- Passed with documented skip: `SKIP=backend-pytest pre-commit run --files $(git diff --cached --name-only --diff-filter=ACMR)`.
- Expected command issue, rerun separately: mixing backend test paths with repo-root `tests/harness/test_repo_contracts.py` in one pytest invocation selected `ai-pic-backend` as root and triggered a pytest-alembic rootpath collection error.

## Next Steps

- Continue scanning for import-chain-proven dead modules and compatibility shims.

## Linked Commits

- Pending.
