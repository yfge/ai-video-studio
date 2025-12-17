---
id: 2025-12-17T11-47-31Z-script-ux-streamline
date: 2025-12-17T11:47:31Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, ux]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Streamlined script detail user path with guided step cards and default scenes tab"
---

## User Prompt

http://localhost:8089/episodes/923aee9db8c748129b06e1b611ff6f76 下的剧本进入后动线混乱，请优化。

## Goals

- Clarify the primary actions on the script detail page (scenes vs. structure vs. storyboard).
- Make the first screen land where users can continue their workflow without hunting for entry points.

## Changes

- Defaulted the script page to the “场景详情” tab and added helper actions to jump between details and structure views.
- Inserted a “步骤 1/2/3” quick-nav strip guiding users to scene details, structure editing, or direct storyboard management.

## Validation

- `npm run lint` (ai-pic-frontend): pass.

## Next Steps

- Reload the script detail page from the episode and confirm the new step cards + default scenes tab make the flow clearer; verify buttons jump to the right view/storyboard.

## Linked Commits

- Pending
