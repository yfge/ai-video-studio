---
id: 2025-12-19T10-12-59Z-episode-story-link
date: 2025-12-19T10:13:04Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, routing]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
summary: "Use story business id in episode header navigation"
---

## User Prompt

- Story link at `http://localhost:8089/stories/23` was not replaced with the business UUID.

## Goals

- Navigate from episode detail to story detail using the business UUID when available.

## Changes

- Updated the episode header story navigation to push `story_business_id` with a numeric fallback.

## Validation

- `npm run lint` (ai-pic-frontend).
- `./docker/build_prod_images.sh` succeeded (tag `95777a8`).
- Chrome MCP: opened `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7`, clicked "Return to story", verified URL changed to `http://localhost:8089/stories/6d7c528b4b064a5f99689f095f5bef90`.

## Next Steps

- None.

## Linked Commits

- Pending
