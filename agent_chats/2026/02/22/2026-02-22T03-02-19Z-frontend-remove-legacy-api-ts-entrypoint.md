---
id: 2026-02-22T03-02-19Z-frontend-remove-legacy-api-ts-entrypoint
date: 2026-02-22T03:02:19Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, lint, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - tasks.md
summary: "Removed the legacy src/utils/api.ts compatibility entrypoint after migration completion and updated task board metrics accordingly."
---

## User Prompt

继续

## Goals

- Continue API de-legacy work after endpoint/type migrations.
- Remove the final `src/utils/api.ts` legacy compatibility surface.
- Keep task board metrics aligned with the actual repository state.

## Changes

- Deleted `ai-pic-frontend/src/utils/api.ts`.
  - The project now uses only modular API surfaces:
    - `@/utils/api/endpoints`
    - `@/utils/api/types`
    - `@/utils/api/client`
- Updated `tasks.md`:
  - `src/utils/api.ts` KPI updated from `2784 -> 20` to `2784 -> 0`.
  - Refactor progress item updated from "compat shim" to "legacy entrypoint removed".

## Validation

- Legacy import scan:
  - `rg -n "@/utils/api(\\.ts)?['\"]|from ['\"].*utils/api(\\.ts)?['\"]" ai-pic-frontend/src ai-pic-frontend/tests` => no matches.
- Frontend lint:
  - `cd ai-pic-frontend && npm run lint` => pass (warnings only).
- Production build gate:
  - `./docker/build_prod_images.sh` => pass; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `ab07073`.
- Chrome MCP E2E on repo dev server (`3100`):
  - Logged in via `geyunfei / Gyf@845261`.
  - Opened `/stories/be3f0a9a256e430b8e3ce24a8022da1f`.
  - Verified story detail rendered with `导出知乎体小说` section present.

## Next Steps

- Keep enforcing no-legacy-import policy and continue modular cleanup for remaining API subdomain files where needed.
- Prioritize next large-file refactor target (`episodes/[id]/storyboard/page.tsx`).

## Linked Commits

- refactor(frontend): remove legacy api.ts entrypoint
