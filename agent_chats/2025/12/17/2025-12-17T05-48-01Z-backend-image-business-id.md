---
id: 2025-12-17T05-48-01Z-backend-image-business-id
date: 2025-12-17T05:48:01Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/images.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
summary: "Add business_id-aware image endpoints and soft-delete handling"
---

## User Prompt

- Extend business_id support to remaining endpoints (image-related), keep soft-delete semantics.

## Goals

- Allow image/virtual_ip_image APIs to resolve resources via business_id and enforce soft-delete filtering.
- Avoid hard deletes while keeping access control intact.

## Changes

- Images API: helper to resolve by id/business_id; added business_id GET/download/delete routes; delete now soft-deletes and checks is_deleted for detail/download.
- Virtual IP images: unified identifier parser; routes accept virtual_ip business_id; image fetch supports image business_id; new records set virtual_ip_business_id; deletes remain soft-delete.

## Validation

- Not run (API surface changes only).

## Next Steps

- Consider adding business_id paths for any remaining assets if needed; run API smoke tests.

## Linked Commits

- (pending)
