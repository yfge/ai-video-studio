---
id: 2025-12-07T14-57-49Z-script-scenes-ux
date: 2025-12-07T14:57:49Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, scripts, ux]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Clarify script scenes tab interaction so users know there are multiple scenes"
---

## User Prompt

这个交互太傻叉了，优化一下

## Goals

- Make it obvious in the “场景详情” tab that there are multiple scenes and that users can click to switch between them.

## Changes

- On the script detail page scenes tab, added a small helper text under the `SceneStructurePanel` when `scenes.length > 1`, explaining that there are N scenes and that the left-side “场景 X” cards can be clicked to switch the details panel.

## Validation

- Manually reloaded `/scripts/12` in Chrome: “场景详情” now shows the helper sentence above the scene list while still rendering scene 1 details by default; other scenes remain clickable in the left list.

## Next Steps

- If confusion persists, consider adding a compact “场景 X / N” indicator near the detail header or a hover state/tutorial for first-time users.

## Linked Commits

- pending
