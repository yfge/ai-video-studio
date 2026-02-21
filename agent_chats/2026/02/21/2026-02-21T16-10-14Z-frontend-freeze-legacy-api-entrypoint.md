---
id: 2026-02-21T16-10-14Z-frontend-freeze-legacy-api-entrypoint
date: 2026-02-21T16:10:14Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, lint, governance, "[refactor]"]
related_paths:
  - ai-pic-frontend/eslint.config.mjs
  - tasks.md
summary: "Added ESLint guard to block legacy '@/utils/api' imports and marked the freeze task complete."
---

## User Prompt

继续

## Goals

- Continue after legacy import cleanup with a guard that prevents regression.
- Enforce the rule that new API usage must go through split modules (`endpoints/types/client`).
- Update task board status with concrete completion evidence.

## Changes

- Added `legacy-api-import-guard` in `ai-pic-frontend/eslint.config.mjs`:
  - Enables `no-restricted-imports` for `@/utils/api` and `@/utils/api.ts`.
  - Message points contributors to `@/utils/api/endpoints`, `@/utils/api/types`, and `@/utils/api/client`.
- Updated `tasks.md` to mark the freeze task as complete with the lint rule reference.

## Validation

- `rg -n 'from "@/utils/api"' ai-pic-frontend/src | wc -l` => `0`.
- `pre-commit run --files ai-pic-frontend/eslint.config.mjs tasks.md` => pass.
- `cd ai-pic-frontend && npm run lint` => pass (warnings only, no errors).
- `./docker/build_prod_images.sh` => pass; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `ef383b0`.
- Browser validation复盘（按“不要嘴硬”执行）:
  - Initially assumed `http://127.0.0.1:3000` was this repo’s frontend.
  - Verified via process inspection that port `3000` was occupied by another project (`ai-shifu`), then switched to launching this repo at `3100`.
  - Chrome MCP commands (`new_page`/`navigate_page`/`take_snapshot`) timed out repeatedly during this turn, so no reliable new MCP E2E evidence could be produced after the timeout started.

## Next Steps

- Add a focused endpoint module for story novel export/download APIs to avoid raw `httpClient` calls in utility files.
- Consider adding a repo-level guard script in CI to fail on legacy import patterns even before ESLint runs.

## Linked Commits

- refactor(frontend): freeze legacy api entrypoint
