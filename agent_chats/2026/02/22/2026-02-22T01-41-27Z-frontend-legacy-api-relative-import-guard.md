---
id: 2026-02-22T01-41-27Z-frontend-legacy-api-relative-import-guard
date: 2026-02-22T01:41:27Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, lint, "[refactor]"]
related_paths:
  - ai-pic-frontend/eslint.config.mjs
  - ai-pic-frontend/src/app/login/page.tsx
  - ai-pic-frontend/src/app/admin/stats/page.tsx
  - ai-pic-frontend/src/app/admin/users/page.tsx
  - ai-pic-frontend/src/types/api-extensions.d.ts
  - tasks.md
summary: "Migrated remaining relative legacy api entrypoint imports and hardened lint guard without blocking split API modules."
---

## User Prompt

继续

## Goals

- Continue the frontend API de-legacy work after clearing `from "@/utils/api"` imports.
- Migrate remaining relative legacy imports (`../../utils/api` style) to split modules.
- Keep lint protection for frozen legacy entrypoints while allowing `endpoints/types/client` imports.

## Changes

- Updated remaining app pages to split API imports:
  - `ai-pic-frontend/src/app/login/page.tsx`
  - `ai-pic-frontend/src/app/admin/stats/page.tsx`
  - `ai-pic-frontend/src/app/admin/users/page.tsx`
- Updated `ai-pic-frontend/src/types/api-extensions.d.ts`:
  - Removed `declare module "@/utils/api"` augmentation.
  - Kept augmentation on `@/utils/api/types` only.
- Hardened `ai-pic-frontend/eslint.config.mjs` legacy import guard:
  - Added restrictions for `@/utils/api/index` and `@/utils/api/index.ts`.
  - Added exact relative-path restrictions for `utils/api(.ts|/index)` variants.
  - Fixed an over-broad pattern that initially blocked legal split-module imports.
- Updated `tasks.md`:
  - Noted freeze coverage includes alias + relative legacy entrypoints.
  - Marked acceptance metric (`169 -> <=100`) complete with current import count at 0.

## Validation

- Legacy entrypoint import scan:
  - `rg -n "from ['\"].*(@/utils/api(\\.ts|/index(\\.ts)?)?|\\.\\.?/.*utils/api(\\.ts|/index(\\.ts)?)?)['\"]" ai-pic-frontend --glob '*.{ts,tsx,js,mjs,d.ts}'` => no matches.
- Frontend lint:
  - `cd ai-pic-frontend && npm run lint` => pass (warnings only, no errors).
- Production build gate:
  - `./docker/build_prod_images.sh` => pass; backend/frontend images built & pushed for `linux/amd64,linux/arm64` with tag `97a0ade`.
- Chrome MCP E2E (dev server `3100`):
  - Logged in with `geyunfei / Gyf@845261`.
  - Verified `/stories/be3f0a9a256e430b8e3ce24a8022da1f` renders story detail and novel export/history sections.
  - Verified `/admin/stats` and `/admin/users` render and load data cards/list without runtime import failures.

## Next Steps

- Continue shrinking `ai-pic-frontend/src/utils/api.ts` by migrating remaining API groups to domain split modules.
- After full migration, deprecate and remove the legacy compatibility surface entirely.

## Linked Commits

- refactor(frontend): block relative legacy api entry imports
