---
id: 2026-02-22T01-58-01Z-frontend-api-ts-compat-shim
date: 2026-02-22T01:58:01Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, docs, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/README.md
  - tasks.md
summary: "Reduced legacy src/utils/api.ts from monolith to a 20-line compatibility shim and updated docs/task tracking to reflect completion."
---

## User Prompt

继续

## Goals

- Continue legacy frontend API cleanup after clearing old entrypoint imports.
- Shrink `src/utils/api.ts` from monolithic implementation to compatibility-only surface.
- Update project docs and task board to reflect the migration status.

## Changes

- Replaced `ai-pic-frontend/src/utils/api.ts` (2784 lines) with a 20-line compatibility shim:
  - Re-export HTTP client utilities from `./api/client`.
  - Re-export types from `./api/types`.
  - Re-export endpoints from `./api/endpoints`.
  - Added deprecation notice directing usage to split modules.
- Updated `ai-pic-frontend/README.md` development guide:
  - API extension instruction now points to `src/utils/api/endpoints/*`, `src/utils/api/types/*`, and `src/utils/api/client.ts`.
- Updated `tasks.md`:
  - Marked `src/utils/api.ts` line-reduction KPI complete (`2784 -> 20`).
  - Marked refactor item complete (legacy file now compatibility layer).
  - Adjusted status summary and freeze note wording to match current state.

## Validation

- `cd ai-pic-frontend && npm run lint` => pass (warnings only).
- `./docker/build_prod_images.sh` => pass; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `58bf460`.
- Chrome MCP E2E on repo dev server (`3100`):
  - Opened `/login` (session user `geyunfei`).
  - Opened `/stories/be3f0a9a256e430b8e3ce24a8022da1f`.
  - Verified story detail rendered and `导出知乎体小说` section present.

## Next Steps

- Evaluate whether `src/utils/api.ts` compatibility shim can be fully removed after one stable cycle with no external callers.
- Continue large-file refactor priorities (`storyboard/page.tsx`, backend `scripts_legacy.py`).

## Linked Commits

- refactor(frontend): shrink legacy api.ts to compat shim
