---
id: 2025-12-17T12-13-45Z-storyboard-audio-range
date: 2025-12-17T12:13:45Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, bugfix]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Fix timeline audio fragment calc ordering to avoid ReferenceError"
---

## User Prompt

ReferenceError: Cannot access 'timelineBeatWindow' before initialization on storyboard page.

## Goals

- Remove TDZ error by computing scene audio fragment after timeline window is available.

## Changes

- Moved scene audio range/url memoization below the `timelineBeatWindow` definition.

## Validation

- `npm run lint` (ai-pic-frontend): pass.

## Next Steps

- Reload storyboard page to confirm the ReferenceError is gone and audio clip still scopes to the selected scene window.

## Linked Commits

- Pending
