## User Prompt

PLEASE IMPLEMENT THIS PLAN: 故事列表改为 IP/环境式二级页面。

## Goals

- Change `/stories` from a rail-and-embedded-detail workspace into a list entry page.
- Keep `/stories/[id]` as the detail page for story production, readiness checks, and episode generation.
- Preserve existing story generation and deletion behavior.

## Changes

- Reworked `StoryProductionBoard` to render a story list panel with genre/status filters and card-style entries.
- Split the list panel into `StoryListSection` to keep the page component within repository size limits.
- Removed query-string story selection and embedded `StoryProductionDetail` rendering from `/stories`.
- Kept `StoryGenerateForm` on the list page and routed story detail actions to `/stories/{business_id}`.
- Restored an explicit episode generation entry: story cards now link to `/stories/{business_id}?generate=episodes`, and story detail auto-expands the episode generation panel for that query.

## Validation

- `cd ai-pic-frontend && npm run lint` passed with existing warnings only.
- `cd ai-pic-frontend && npm run build` passed.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/stories/StoryProductionBoard.tsx ai-pic-frontend/src/components/features/stories/StoryListSection.tsx agent_chats/2026/05/08/2026-05-08T06-16-13Z-story-secondary-page.md` passed.
- `pre-commit run --all-files` was attempted before commit. It failed on pre-existing repository-wide backend lint/import issues and hook-modified unrelated files; those unrelated hook changes were reverted before staging this commit.
- Browser validation on `http://localhost:3010/stories` confirmed the page renders the list entry layout with no embedded `剧集生产状态` detail.
- Browser validation clicked a story detail link and confirmed `/stories/be3f0a9a256e430b8e3ce24a8022da1f` shows `剧集生产状态`, `IP 生产准备`, and existing `进入时间轴` links.
- Browser validation opened the `AI生成故事` creation overlay and the delete confirmation without confirming deletion.
- Follow-up browser validation confirmed story cards expose `生成剧集`; clicking it opens `/stories/be3f0a9a256e430b8e3ce24a8022da1f?generate=episodes` with the episode generation panel expanded.

## Next Steps

- None.

## Linked Commits

- Pending.
