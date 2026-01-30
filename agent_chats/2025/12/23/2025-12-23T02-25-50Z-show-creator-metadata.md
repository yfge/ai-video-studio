---
id: 2025-12-23T02-25-50Z-show-creator-metadata
date: 2025-12-23T02:25:57Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, frontend, ui]
related_paths:
  - ai-pic-backend/app/schemas/script.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/app/schemas/user.py
  - ai-pic-backend/app/schemas/virtual_ip.py
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentHeader.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentList.tsx
  - ai-pic-frontend/src/components/features/stories/StoryCard.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryDetailHeader.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPListSection.tsx
  - ai-pic-frontend/src/types/api-extensions.d.ts
  - ai-pic-frontend/src/utils/creator.ts
summary: "Display creator metadata for stories, environments, and virtual IPs"
---

## User Prompt

- 在故事、环境、IP 的界面都要显示是谁创建的
- 提交现有的更改

## Goals

- Add creator data to backend response schemas for stories, environments, and virtual IPs.
- Surface creator labels in list/detail UI for stories, environments, and virtual IPs.
- Provide a shared frontend helper for consistent creator display.

## Changes

- Added `UserSummary` schema and exposed `creator` in story, environment, and virtual IP responses via `owner` mapping.
- Added frontend type augmentation and creator label helper for display fallbacks.
- Updated list and detail UI components to render “创建者” consistently.

## Validation

- `npm run lint` (ai-pic-frontend) — pass.
- `pytest` (ai-pic-backend) — timed out at 120s with existing failures (see test output).
- `./docker/build_prod_images.sh` — first run timed out at 120s, rerun succeeded.
- MCP E2E (Chrome): login `geyunfei`/`Gyf@845261`, verified creator on `/virtual-ip` list and `/virtual-ip/{id}` detail, `/environments` list and `/environments/{id}` detail, `/stories` list and `/stories/{id}` detail.

## Next Steps

- Investigate and address failing backend tests if required for release gating.

## Linked Commits

- TBD
