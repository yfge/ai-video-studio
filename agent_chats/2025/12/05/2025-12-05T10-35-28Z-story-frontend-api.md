---
id: 2025-12-05T10-35-28Z-story-frontend-api
date: 2025-12-05T10:35:28Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, api]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/register/page.tsx
summary: "Expose story structure CRUD in frontend API client and wire register success feedback"
---
## User Prompt
前端同步剧本场景/镜头层级、权限钩子与顺序重排、更完整的端到端验证。

## Goals
- Add frontend API wrappers for scenes/beats/shots CRUD (with ordering fields) to enable UI integration.
- Improve register page UX feedback when calling backend.

## Changes
- `src/utils/api.ts`: added update/delete for scenes; create/update/delete for scene beats and shots; included order/shot-number fields for future reordering.
- `src/app/register/page.tsx`: register now calls backend, shows success banner before redirect, and retains error handling.

## Validation
- Not run frontend tests (API wrapper and UI wiring only); backend tests already cover new endpoints.

## Next Steps
- Integrate these API methods into the script detail UI with permissions and ordering interactions; add frontend tests/e2e when UI is wired.

## Linked Commits
- (pending)
