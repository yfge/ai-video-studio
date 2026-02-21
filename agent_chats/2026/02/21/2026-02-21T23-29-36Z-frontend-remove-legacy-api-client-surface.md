---
id: 2026-02-21T23-29-36Z-frontend-remove-legacy-api-client-surface
date: 2026-02-21T23:29:36Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, tests, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/utils/api/index.ts
  - ai-pic-frontend/tests/sceneStructurePanel.test.tsx
  - tasks.md
summary: "Removed legacy apiClient re-export surface from api/index.ts and updated SceneStructurePanel test to use current component paths and apiOverride-only stubs."
---

## User Prompt

继续

## Goals

- Continue frontend API de-legacy work after story novel endpoint migration.
- Remove residual `apiClient` exposure from modular API entrypoint.
- Clean up tests so they no longer depend on legacy `src/utils/api.ts`.

## Changes

- Updated `ai-pic-frontend/src/utils/api/index.ts`:
  - Removed legacy `apiClient` re-export.
  - Updated usage comment to point to `@/utils/api/client`.
- Updated `ai-pic-frontend/tests/sceneStructurePanel.test.tsx`:
  - Removed unnecessary `apiClient` import and monkeypatching.
  - Kept `apiOverride` injection as the only API dependency path.
  - Fixed stale imports to current component locations:
    - `../src/components/shared/modals/AlertModalProvider`
    - `../src/components/features/SceneStructurePanel`
  - Removed unused `fireEvent` import.
- Updated `tasks.md` freeze item text to note `api/index.ts` no longer exports legacy `apiClient`.

## Validation

- `cd ai-pic-frontend && npm run test -- tests/sceneStructurePanel.test.tsx` => pass.
- `cd ai-pic-frontend && npm run lint` => pass (warnings only).
- `pre-commit run --files ...` => pass.
- `./docker/build_prod_images.sh` => pass; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `a19b104`.
- Chrome MCP E2E on repo dev server (`3100`):
  - Opened `/login`.
  - Opened `/stories/be3f0a9a256e430b8e3ce24a8022da1f`.
  - Verified story detail page and “导出知乎体小说 / 历史导出” sections render normally.

## Next Steps

- Continue reducing `src/utils/api.ts` by extracting remaining legacy API groups and shrinking file size toward target.
- Consider deprecating/removing `src/utils/api.ts` after confirming no non-test runtime consumers remain.

## Linked Commits

- refactor(frontend): remove legacy api client surface
