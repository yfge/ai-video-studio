---
id: 2025-12-05T15-54-05Z-storyboard-beat-badges
date: 2025-12-05T15:54:05Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, testing, storyboard]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/tests/storyboardStructure.e2e.ts
summary: "Display beat/shot identifiers on storyboard frames and add badge test"
---
## User Prompt
yesd

## Goals
- Surface beat/shot identifiers on storyboard frames when backend provides them.
- Add a test to validate the new badges.

## Changes
- Frame cards now render beat_id, shot_id, and shot_number badges when present.
- Added a test to ensure badges render for mocked frame data.

## Validation
- ai-pic-frontend: npm test

## Next Steps
- Enable full E2E once backend frames expose beat_id/shot_id; assert linkage to structured beats/shots.

## Linked Commits
- (pending)
