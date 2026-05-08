## User Prompt

PLEASE IMPLEMENT THIS PLAN: 故事列表改为 IP/环境式二级页面。

Follow-up: 移除剧集生成的聚焦角色选择。

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
- Follow-up adjusted the entry to include `#episode-generation` and scroll the expanded panel into view, so clicking `生成剧集` produces an immediate visible transition.
- Follow-up layout change moved the episode generation panel from the right inspector into the main story detail content before `剧集生产状态`; the inspector now focuses on readiness checks.
- Follow-up removed the episode focus-character picker entirely. Episode generation now relies on the story's own character context and no longer sends frontend-selected `focus_characters`.

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
- Follow-up validation after scroll-anchor change: `npm run lint`, `npm run build`, and diff contracts passed. Browser login replay was blocked by the browser tool virtual clipboard issue, so the visible-scroll change was verified by build/static checks rather than a full authenticated click replay.
- Follow-up local checks for focus-character removal passed: `cd ai-pic-frontend && npm run lint` (19 existing warnings, 0 errors), `cd ai-pic-frontend && npm run test` (10 tests passed), `cd ai-pic-frontend && npm run build`, `python scripts/check_repo_contracts.py --mode diff agent_chats/2026/05/08/2026-05-08T06-16-13Z-story-secondary-page.md ai-pic-frontend/src/components/features/stories/StoryProductionDetail.tsx ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanel.tsx ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanelFields.tsx ai-pic-frontend/src/hooks/useStoryEpisodeGeneration.ts`, and `git diff --check`.
- Follow-up browser validation attempted Chrome DevTools first, but the local DevTools endpoint returned `HTTP Not Found`; validation fell back to Playwright with the system Chrome executable.
- Playwright path: `http://localhost:3000/stories/be3f0a9a256e430b8e3ce24a8022da1f?generate=episodes#episode-generation` opened with the episode generation panel expanded; the form did not contain `聚焦角色`; the story header still showed associated IP chips (`IP: 未命名 IP` twice).
- Playwright intercepted `POST /api/v1/episodes/prompt/preview` and `POST /api/v1/episodes/generate-async`; both request bodies contained only `episode_count`, `episode_duration`, `pacing`, `plot_complexity`, `story_id`, and `temperature`, with no `focus_characters`.
- Browser evidence saved under `artifacts/runs/story-focus-removal-20260508T074057Z/`; console had no warnings or errors for the verified path.

## Next Steps

- None.

## Linked Commits

- Pending.
