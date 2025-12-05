---
id: 2025-12-05T10-28-26Z-auth-register-api
date: 2025-12-05T10:28:26Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, backend, auth]
related_paths:
  - ai-pic-frontend/src/app/register/page.tsx
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Wire frontend register page to auth API and harden story structure validations"
---
## User Prompt
注册用户没有调用 接口？

## Goals
- Make the frontend register page actually call the backend auth register API.
- Harden scene/beat/shot service validations and bubble meaningful errors via API.

## Changes
- Frontend register page now submits to `/api/v1/auth/register` via `api.register`, shows server errors, and redirects to login on success.
- Backend scene/beat/shot creation/update now checks script/scene ownership, duplicate order/shot numbers, and beat-scene consistency; API returns 400/404 with clear messages.

## Validation
- Backend: `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py tests/test_story_structure_service.py tests/test_user_management.py::TestUserRegistration -q`
- Frontend: not run (API call wiring change only).

## Next Steps
- Add frontend feedback for pending/approved status after registration if needed; optionally add e2e test for register/login.

## Linked Commits
- (pending)
