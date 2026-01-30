---
id: 2025-12-05T14-26-00Z-storyboard-structure-align
date: 2025-12-05T14:26:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard, permissions]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/components/SceneStructurePanel.tsx
summary: "Align storyboard view with structured scenes and add permission-aware toasts"
---

## User Prompt

align storyboard view with structured scenes and add richer permission-aware toasts.

## Goals

- Use structured scene data for scene lists and storyboard context.
- Surface clearer permission-aware feedback for scene/beat/shot edits.

## Changes

- Script detail page now prefers structured scenes for scene lists and storyboard annotations, and warns non-admin users when in read-only mode; structure panel updates parent when data loads.
- Scene structure panel now emits toasts for read-only attempts, CRUD successes/failures, and exposes loaded data via callback.

## Validation

- npm run lint

## Next Steps

- Tie storyboard frame metadata to structured beats/shots when available and add E2E covering CRUD + permissions.

## Linked Commits

- (pending)
