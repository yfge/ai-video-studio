---
id: 2025-12-17T11-33-09Z-script-focused-scene
date: 2025-12-17T11:33:09Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, script]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Restore focused scene state after removing storyboard tab"
---

## User Prompt

Add follow-up fix so script page works after removing embedded storyboard workspace.

## Goals

- Bring back focused scene state to avoid runtime errors after prior cleanup.
- Keep script detail navigation for scenes functional.

## Changes

- Reintroduced focused scene state on script detail page and derived active scene via memoization to fix undefined references.

## Validation

- Ran `npm run lint` in ai-pic-frontend: passed.

## Next Steps

- After login, quickly verify the script detail page loads scenes list without console errors.

## Linked Commits

- Pending
