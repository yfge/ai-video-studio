---
id: 2025-12-17T05-55-13Z-backend-image-fix
date: 2025-12-17T05:55:13Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
summary: "Fix virtual IP image signature ordering and persist business_id for async variants"
---

## User Prompt

- Continue soft-delete/business_id rollout; backend was failing to start due to SyntaxError in virtual_ip_images.py.

## Goals

- Unblock backend startup by fixing the invalid function signature.
- Ensure async virtual IP image variant tasks also persist virtual_ip_business_id.

## Changes

- Reordered update_virtual_ip_image parameters so required body (image_update) precedes optional image_business_id, resolving the SyntaxError.
- Celery variant task now saves virtual_ip_business_id when creating VirtualIPImage records.

## Validation

- `python -m compileall ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py`

## Next Steps

- Restart backend and re-run image endpoints; follow up with full E2E verification once backend is up.

## Linked Commits

- (pending)
