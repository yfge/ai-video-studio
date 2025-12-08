---
id: 2025-12-08T07-48-10Z-storyboard-normalized
date: "2025-12-08T07:48:10Z"
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
summary: "Enforced normalized storyboard flow and removed import-based entry points"
---

## User Prompt

分镜管理以及分镜生成都使用新的规范化结构，不要再有什么导入相关的功能了

## Goals

- Ensure storyboard management and generation rely solely on the normalized scene/shot structure.
- Remove import-based shortcuts from old JSON scenes.
- Align user-facing copy with the normalized-only flow.

## Changes

- Simplified the storyboard page to always operate on normalized scenes/shots; removed the import button and legacy script-scene fallback.
- Added guards so generation (per-scene/all scenes, images/video) requires normalized scenes and a selected normalized scene; normalized scene list now drives selection state.
- Dropped the front-end `seedScenesFromJson` API surface and cleaned Episode page copy to remove import mentions.

## Validation

- `pre-commit run --files ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx ai-pic-frontend/src/utils/api.ts ai-pic-frontend/src/app/episodes/[id]/page.tsx`

## Next Steps

- If normalized scenes are absent, guide users to create them in the story structure workflow before storyboard generation.

## Linked Commits

- (pending)
