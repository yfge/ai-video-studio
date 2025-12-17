---
id: 2025-12-17T11-58-08Z-scene-combined-view
date: 2025-12-17T11:58:08Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, script]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Scene list now shows per-scene structure and text details side by side"
---

## User Prompt

http://localhost:8089/scripts/b40daa0d5f9848e0ae6c90bc02d7bb45 改成场景列表，选中后同时展示结构化信息与文本详情。

## Goals

- Reduce the scenes tab to a clear list + combined detail view.
- Show both structured beats/shots and textual dialogue/directions for the selected scene.

## Changes

- Defaulted to the scenes tab; added structure loading via `storyStructureAPI` and per-scene beats/shots fetches.
- Replaced the old toggle with a single list/detail layout: left scene list, right cards for文本详情 plus结构化信息 (beats/shots summaries) and optional inline structure editor toggle.
- Kept quick step cards; buttons now jump to scenes tab and optionally open structure editor.

## Validation

- `npm run lint` (ai-pic-frontend): pass.

## Next Steps

- Reload脚本页，点选场景，确认右侧同时出现结构化信息（节拍/镜头）和文本详情；若要编辑结构点击“编辑结构”展开面板。

## Linked Commits

- Pending
