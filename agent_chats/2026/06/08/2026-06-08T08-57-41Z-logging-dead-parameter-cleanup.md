---
id: 2026-06-08T08-57-41Z-logging-dead-parameter-cleanup
date: "2026-06-08T08:57:41Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - backend
  - dead-code
  - logging
related_paths:
  - ai-pic-backend/app/core/logging.py
summary: Removed an unused setup_logging parameter reported by static dead-code scanning.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Continue function-level dead-code cleanup after module-level dead-code removal.
- Remove only a parameter that is unused in implementation and has no repository callers.
- Leave framework-required pytest fixture and callback parameters untouched.

## Changes

- Removed the unused `max_log_file_size` parameter from `setup_logging()`.
- Removed the matching stale docstring entry.

## Validation

- `rg -n "max_log_file_size" ai-pic-backend/app ai-pic-backend/tests scripts docs || true`
- `ai-pic-backend/.venv/bin/python -m pyflakes ai-pic-backend/app ai-pic-backend/tests ai-pic-backend/scripts scripts`
- `ai-pic-backend/.venv/bin/python -m compileall -q ai-pic-backend/app scripts`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/core/logging.py agent_chats/2026/06/08/2026-06-08T08-57-41Z-logging-dead-parameter-cleanup.md`
- `SKIP=backend-pytest pre-commit run --files ai-pic-backend/app/core/logging.py agent_chats/2026/06/08/2026-06-08T08-57-41Z-logging-dead-parameter-cleanup.md`

## Next Steps

- Continue function/export-level dead-code review with repository call-chain proof.
- Do not remove pytest fixture parameters or framework callback parameters solely because static scanners report them as unused.

## Linked Commits

- This commit: `chore(backend): remove dead logging parameter`.
