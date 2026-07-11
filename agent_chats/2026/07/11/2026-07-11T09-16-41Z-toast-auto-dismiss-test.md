---
id: 2026-07-11T09-16-41Z-toast-auto-dismiss-test
date: "2026-07-11T09:16:41Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - frontend
  - tests
related_paths:
  - ai-pic-frontend/tests/toastProvider.test.tsx
summary: Stabilized the toast auto-dismiss test by awaiting its timer-driven React update inside act.
---

## User Prompt

先提交现有变更

## Goals

- Commit the remaining toast test change separately from the production canvas work.
- Replace the ineffective timeout increase with a deterministic assertion that exits cleanly.

## Changes

- Imported Testing Library's `act` helper.
- Awaited the configured auto-dismiss timer inside `act`, then asserted that the toast was removed.
- Kept production notification behavior unchanged.

## Validation

- `cd ai-pic-frontend && npx tsx --test tests/toastProvider.test.tsx` -> 5 tests passed and the process exited normally in about one second.
- `cd ai-pic-frontend && npm run lint` -> passed with 3 existing warnings and no errors.
- Scoped pre-commit hooks -> passed after applying Prettier's import formatting.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> backend and frontend images built locally without push; the frontend build included `/canvas`.

## Next Steps

- None.

## Linked Commits

- Pending.
