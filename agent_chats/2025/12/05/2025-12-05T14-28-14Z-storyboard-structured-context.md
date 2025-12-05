---
id: 2025-12-05T14-28-14Z-storyboard-structured-context
date: 2025-12-05T14:28:14Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard, story-structure]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Use structured scenes to annotate storyboard groups"
---
## User Prompt
继续

## Goals
- Make storyboard groups reflect structured scene metadata when available.

## Changes
- Added structured scene lookup to annotate storyboard groups with slug lines, beat/shot counts, and a notice that structured data drives the view.
- Storyboard view now shows a banner when structured scenes are loaded.

## Validation
- npm run lint

## Next Steps
- Hook storyboard frames to specific beats/shots once backend provides links; add E2E for structured CRUD + storyboard alignment.

## Linked Commits
- (pending)
