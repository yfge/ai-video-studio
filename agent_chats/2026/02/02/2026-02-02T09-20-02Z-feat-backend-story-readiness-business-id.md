---
id: 2026-02-02T09-20-02Z-feat-backend-story-readiness-business-id
date: 2026-02-02T09:20:02Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories/readiness.py
summary: "Add story readiness-check and quick-fix endpoints keyed by business_id"
---

## User Prompt

commit and push

## Goals

- Support story readiness checks and quick-fix flows when callers only have `business_id`.
- Keep endpoints thin and reuse existing story lookup logic.

## Changes

- Added `/stories/business/{story_business_id}/readiness-check`.
- Added `/stories/business/{story_business_id}/quick-fix`.

## Validation

- `cd ai-pic-backend && pytest`

## Next Steps

- Add integration coverage for the new business_id routes if we start calling them from frontend flows.

## Linked Commits

- pending
