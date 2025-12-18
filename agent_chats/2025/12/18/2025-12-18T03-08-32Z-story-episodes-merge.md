---
id: 2025-12-18T03-08-32Z-story-episodes-merge
date: 2025-12-18T03:08:32Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, stories]
related_paths:
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
summary: "Merged episode outline and overview into one list on story page and reran prod build."
---

## User Prompt
http://localhost:8089/stories/6d7c528b4b064a5f99689f095f5bef90 把剧集大纲和剧集概览合并 ，只有一个列表。

## Goals
- Combine episode outline and actual episode overview into a single list on the story detail page.
- Keep outline beats, summary, scripts, and scenes visible together.
- Ensure lint/build (including docker prod build) remain green.

## Changes
- Added merged `combinedEpisodes` view to `stories/[id]` page: displays title/summary from episode or outline, outline beats preview, scenes/snippets, scripts links, and unified count.
- Removed separate outline block and standalone episode grid; consolidated into one list.

## Validation
- `npm run lint` (ai-pic-frontend) — pass.
- `./docker/build_prod_images.sh` — pass (images pushed with tag e251443).

## Next Steps
- Optional: add loading/empty states for outline beats when episode exists but outline missing.

## Linked Commits
- (pending)
