---
id: 2026-02-06T09-13-18Z-frontend-episode-characters-api
date: 2026-02-06T09:13:18Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api]
related_paths:
  - ai-pic-frontend/src/utils/api/episodeCharacters.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceCharactersTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/CharacterFormModal.tsx
  - ai-pic-frontend/src/components/features/episode/CharacterCommonFields.tsx
  - ai-pic-frontend/src/components/features/episode/CharacterRow.tsx
summary: "Fix Episode Characters API client usage and modal typing; ensure prod build passes."
---

## User Prompt

"ai-pic-frontend/src/utils/api/episodeCharacters.ts 这个文件没有提交"

## Goals

- Commit the missing `episodeCharacters.ts` changes.
- Ensure frontend production build passes (docker prod image build gate).

## Changes

- Updated Episode Characters API helper to use the new `httpClient` wrapper and `/api/v1/...` endpoints.
  - `ai-pic-frontend/src/utils/api/episodeCharacters.ts`
- Fixed Next.js production build TypeScript error in episode workspace characters tab by splitting modal/row components and typing `onSubmit` per mode.
  - `ai-pic-frontend/src/components/features/episode/WorkspaceCharactersTabContent.tsx`
  - `ai-pic-frontend/src/components/features/episode/CharacterFormModal.tsx`
  - `ai-pic-frontend/src/components/features/episode/CharacterCommonFields.tsx`
  - `ai-pic-frontend/src/components/features/episode/CharacterRow.tsx`

## Validation

- Frontend lint:
  - `cd ai-pic-frontend && npm run lint` (warnings only).
- Production image build gate:
  - `./docker/build_prod_images.sh` (backend + frontend buildx build/push succeeded).
- Chrome E2E (Dev Docker stack at `http://localhost:8089`, user `geyunfei`):
  - Login -> Stories -> open story "爱情喜剧" -> enter Episode 1 workspace -> open "临时角色" tab.
  - Verified characters list loads.
  - Create a temporary character (VirtualIP ID `1`) -> edit personality -> delete the created character.

## Next Steps

- (Optional) Address Next.js warning about multiple lockfiles in the repo root vs `ai-pic-frontend/`.

## Linked Commits

- (pending)
