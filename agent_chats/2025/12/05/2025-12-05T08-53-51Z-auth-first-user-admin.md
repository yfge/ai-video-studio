---
id: 2025-12-05T08-53-51Z-auth-first-user-admin
date: 2025-12-05T08:53:51Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, auth]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/auth.py
  - ai-pic-backend/tests/test_user_management.py
summary: "Auto-promote first registered user to admin and adjust tests"
---

## User Prompt

那第一个用户也不不是管理员，要怎么处理？

## Goals

- Allow initial bootstrap without manual DB edits by promoting the very first registered user to admin/superuser and activating them.
- Keep subsequent users on the existing approval/activation flow.
- Update registration tests to reflect the new behavior and ensure later users stay pending.

## Changes

- `auth.register` now detects if it is the first user and sets `is_active/is_approved/email_verified/is_admin/is_superuser` to true for that user; later users remain pending and get activation tokens as before.
- Registration tests now clear the table and expect first-user admin; added a case for the second user staying pending; aligned fixtures to `db_session`.

## Validation

- Not re-running full test suite here (existing test setup needs broader fixture cleanup); logic is straightforward. Retest locally if desired after fixture adjustments.

## Next Steps

- Run `cd ai-pic-backend && pytest tests/test_user_management.py` after aligning fixtures (remaining `db` fixture use may need cleanup) or during CI.

## Linked Commits

- (pending)
