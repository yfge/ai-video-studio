---
id: 2025-12-05T15-09-04Z-storyboard-e2e-placeholder
date: 2025-12-05T15:09:04Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [testing, storyboard]
related_paths:
  - ai-pic-frontend/tests/storyboardStructure.e2e.ts
  - ai-pic-backend/MIGRATION_SYSTEM_GUIDE.md
summary: "Add placeholder E2E scaffold for storyboard beat/shot links and document rollback drills"
---
## User Prompt
add E2E coverage tying storyboard frames to beat/shot links (when backend exposes them) and keep migration rollback drills recorded.

## Goals
- Prepare E2E scaffold for storyboard-beat/shot alignment without blocking on missing backend metadata.
- Document migration rollback drill steps and record-keeping expectations.

## Changes
- Added a skipped E2E test placeholder describing the beat/shot linkage flow once backend frame metadata is available.
- Updated migration guide with a rollback drill checklist and storage guidance for reports/logs.

## Validation
- (not run; placeholder test is skipped by default)

## Next Steps
- Wire storyboard frames to beat_id/shot_id when backend exposes them, then enable the E2E.
- Store future migration drill reports under `backups/migration_drills/` and log results in agent_chats.

## Linked Commits
- (pending)
