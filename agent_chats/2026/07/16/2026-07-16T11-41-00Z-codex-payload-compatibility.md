---
id: 2026-07-16T11-41-00Z-codex-payload-compatibility
date: "2026-07-16T11:41:00Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - backend
  - provider
  - codex
  - compatibility
related_paths:
  - ai-pic-backend/app/services/providers/codex_payload.py
  - ai-pic-backend/app/services/providers/codex_provider.py
  - ai-pic-backend/tests/unit/services/providers/test_codex_provider.py
summary: Keep ChatGPT Codex requests compatible with the endpoint by omitting unsupported temperature and output-token fields.
---

## User Prompt

commit

## Goals

- Commit the existing Codex provider compatibility fix as an isolated change.
- Preserve token rotation and retry behavior.
- Avoid changing the public provider method contract used by callers.

## Changes

- Removed `temperature` and `max_output_tokens` from the ChatGPT Codex request
  payload because that endpoint rejects those fields.
- Kept the public `generate_text` parameters intact so existing callers do not
  need to change.
- Extended the provider regression tests to assert both fields remain absent
  before and after a rotated-token retry.

## Validation

- `cd ai-pic-backend && pytest -q --no-cov tests/unit/services/providers/test_codex_provider.py`
  -> `4 passed`.
- Python compilation, Ruff, Black, isort, repository docs, changed-file
  contracts, and `git diff --check` passed for this commit slice.
- Local production backend and frontend Dockerfiles both built successfully
  through Docker BuildKit with `--pull=false`; no image was pushed.

## Next Steps

- None for this compatibility fix.

## Linked Commits

- Included in this commit.
