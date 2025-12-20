---
id: 2025-12-20T05-16-01Z-docs-taskboard-refresh
date: 2025-12-20T05:16:01Z
participants: [human, codex]
models: [gpt-5]
tags: [docs, tasks]
related_paths:
  - AGENTS.md
  - docs/README.md
  - docs/story-structure-api.md
  - docs/storyboard-normalized-toggle.md
  - docs/story-structure-gap-analysis.md
  - docs/REFACTORING_PLAN.md
  - docs/story-structure-discovery-session.md
  - docs/api/google-text-api.md
  - docs/api/open-ai-image.md
  - tasks.md
summary: "Refreshed docs inventory and task board to match current state"
---
## User Prompt
根据项目现状整体梳理 docs 文档，移除不匹配内容；梳理 tasks.md 并移除过期项；更新 AGENTS.md 的文档指向，并提交。

## Goals
- Clean up docs to reflect the current repo state and add a canonical docs index.
- Refresh the task board completion status and remove stale items.
- Update AGENTS.md doc pointers and commit the changes.

## Changes
- Added `docs/README.md` as the canonical docs index.
- Updated story-structure API and storyboard integration docs to reflect current endpoints and behavior.
- Marked the story-structure gap analysis as historical context and aligned task references.
- Refreshed `tasks.md` status overview and per-feature progress to match implemented work.
- Removed stale or irrelevant docs (`docs/REFACTORING_PLAN.md`, `docs/story-structure-discovery-session.md`, `docs/api/google-text-api.md`, `docs/api/open-ai-image.md`).
- Updated `AGENTS.md` to point at the docs index and current doc set.

## Validation
- `./docker/build_prod_images.sh`

## Next Steps
- (optional) Align AGENTS build script path with repo layout if needed.

## Linked Commits
- (pending)
