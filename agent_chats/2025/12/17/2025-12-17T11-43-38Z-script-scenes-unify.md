---
id: 2025-12-17T11-43-38Z-script-scenes-unify
date: 2025-12-17T11:43:38Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, script]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Reorganized script scenes tab into a single toggleable layout"
---

## User Prompt

http://localhost:8089/scripts/b40daa0d5f9848e0ae6c90bc02d7bb45 场景详情太乱，结构化场景/镜头、场景列表、场景详情重复。

## Goals

- Unify the script scenes tab so users don’t see three stacked blocks.
- Keep structure editing available while keeping the main scene detail flow clean.

## Changes

- Added a simple view toggle (“结构化场景 / 镜头” vs “场景文本详情”) so only one block shows at a time.
- Wrapped the structure editor in its own card; scene list + detail stay together in the details view.

## Validation

- `npm run lint` (ai-pic-frontend): pass.

## Next Steps

- Reload the script detail page and switch between “结构化场景/镜头”与“场景文本详情”确认不再堆叠、无白屏。

## Linked Commits

- Pending
