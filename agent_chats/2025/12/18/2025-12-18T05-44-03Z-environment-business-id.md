---
id: 2025-12-18T05-44-03Z-environment-business-id
date: 2025-12-18T05:44:03Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, backend, environments]
related_paths:
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/app/services/story_structure_service.py
summary: "Environment pages now use business_id routing; backend supports business id lookup; images show correctly."
---

## User Prompt
http://localhost:8089/environments/1

1. 传入的不是 businessId
2. 没有显示图片

## Goals
- Make environment detail/list use business_id in routing and API calls.
- Ensure images load/display when navigated via business id.
- Support environment lookup by business_id on backend endpoints (CRUD and image ops).

## Changes
- Backend: added business_id-aware resolver and DTO exposure; list filters soft-deleted; all environment endpoints now accept id or business_id and reuse resolver for images/generate/variants/update/delete.
- Frontend: Environment type now carries business_id; list page routes using business_id; detail page reads raw param (string) and calls APIs with business_id, fixing image fetch/upload/delete/generate when path is business id.
- Rebuilt prod images with new dependency set (tag 5c2c325) after PyJWT addition and env fixes.

## Validation
- `npm run lint` (ai-pic-frontend) — pass.
- `./docker/build_prod_images.sh` — pass; images pushed tag 5c2c325.
- Manual API smoke: login -> token; `/api/v1/ai/models/available?model_type=text_generation` now returns models (no 503) after previous PyJWT fix.

## Next Steps
- Consider exposing business_id in frontend environment creation response for immediate navigation without reload.
- Optional: add E2E page check for environment detail via business_id path.

## Linked Commits
- (pending)
