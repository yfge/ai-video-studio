---
id: 2026-02-22T02-09-19Z-frontend-episode-characters-endpoint-split
date: 2026-02-22T02:09:19Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api, episode, "[refactor]"]
related_paths:
  - ai-pic-frontend/src/utils/api/endpoints/episode-character.endpoints.ts
  - ai-pic-frontend/src/utils/api/types/episode-character.types.ts
  - ai-pic-frontend/src/utils/api/endpoints/index.ts
  - ai-pic-frontend/src/utils/api/types/index.ts
  - ai-pic-frontend/src/utils/api/episodeCharacters.ts
  - ai-pic-frontend/src/hooks/useEpisodeCharacters.ts
  - ai-pic-frontend/src/components/features/episode/CharacterCommonFields.tsx
  - ai-pic-frontend/src/components/features/episode/CharacterFormModal.tsx
  - ai-pic-frontend/src/components/features/episode/CharacterRow.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceCharactersTabContent.tsx
  - ai-pic-frontend/eslint.config.mjs
  - tasks.md
summary: "Split legacy episodeCharacters API module into modular endpoints/types, migrated all callers, deleted legacy file, and added lint guard for the old import path."
---

## User Prompt

继续

## Goals

- Continue frontend API modularization after shrinking `src/utils/api.ts`.
- Remove legacy `@/utils/api/episodeCharacters` entrypoint.
- Migrate episode character API usage to split `endpoints` and `types` modules.

## Changes

- Added new modular files:
  - `ai-pic-frontend/src/utils/api/endpoints/episode-character.endpoints.ts`
  - `ai-pic-frontend/src/utils/api/types/episode-character.types.ts`
- Updated barrel exports:
  - `ai-pic-frontend/src/utils/api/endpoints/index.ts`
  - `ai-pic-frontend/src/utils/api/types/index.ts`
- Migrated all episode-character consumers to modular imports:
  - `ai-pic-frontend/src/hooks/useEpisodeCharacters.ts`
  - `ai-pic-frontend/src/components/features/episode/CharacterCommonFields.tsx`
  - `ai-pic-frontend/src/components/features/episode/CharacterFormModal.tsx`
  - `ai-pic-frontend/src/components/features/episode/CharacterRow.tsx`
  - `ai-pic-frontend/src/components/features/episode/WorkspaceCharactersTabContent.tsx`
- Deleted legacy module:
  - `ai-pic-frontend/src/utils/api/episodeCharacters.ts`
- Hardened lint guard in `ai-pic-frontend/eslint.config.mjs` to block legacy `@/utils/api/episodeCharacters` imports.
- Updated `tasks.md` progress note to record episodeCharacters legacy split completion.

## Validation

- `cd ai-pic-frontend && npm run lint` => pass (warnings only).
- `./docker/build_prod_images.sh` => pass; backend/frontend images built and pushed for `linux/amd64,linux/arm64` with tag `facb4c2`.
- Chrome MCP E2E on repo dev server (`3100`):
  - Opened `/episodes/136/workspace`.
  - Switched to `临时角色` tab and confirmed panel rendered.
  - Clicked `+ 添加角色` and confirmed modal (`添加临时角色`) rendered with expected fields.

## Next Steps

- Keep migrating remaining non-standard API modules to the same `endpoints + types` pattern.
- Consider adding small targeted tests for `useEpisodeCharacters` to protect import-surface regressions.

## Linked Commits

- refactor(frontend): split episode characters api module
