---
id: 2025-12-17T11-03-19Z-frame-input-lock-ui
date: 2025-12-17T11:03:19Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard, timeline]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Keep frame count display in sync with timeline beats when timeline exists."
---

## User Prompt
但是选择以后分镜数没有更新数量，只是禁用了

## Goals
- When an episode timeline exists, reflect the beat-derived frame count in the disabled input so users see the locked value.

## Changes
- Computed `framesPerSceneValue` that prefers the scene's beat count when timeline is present; bound the input's value to this computed number (still disabled when timeline exists).

## Validation
- `npm run lint` (frontend) — pass.

## Next Steps
- After timeline generation, verify the input shows the beat count for the selected scene; if per-scene beats differ, switching scenes should update the displayed count.

## Linked Commits
- (pending)
