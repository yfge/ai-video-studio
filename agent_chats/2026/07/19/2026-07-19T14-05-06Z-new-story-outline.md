---
id: 2026-07-19T14-05-06Z-new-story-outline
date: "2026-07-19T14:05:06Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, story, outline, regression]
related_paths:
  - ai-pic-frontend/src/components/features/stories/StoryProductionDetailParts.tsx
  - ai-pic-frontend/tests/storyOutlineSection.test.tsx
summary: Restore the persisted structured outline for new stories only.
---

## User Prompt

现在在故事页看不到故事大纲了。只处理新故事就可以。

## Goals

- 让新生产故事在故事详情页展示已持久化的结构化故事大纲。
- 不为没有结构化创作合同的历史故事补数据或增加兼容展示。
- 用定向测试和真实浏览器同时证明新、老故事的范围边界。

## Changes

- Added a new-story-only story outline panel to the story production detail page.
- Rendered the persisted `extra_metadata.structured_story_contract` text and list fields without introducing legacy fallback data.
- Added component tests covering both a new story with a contract and a legacy story without one.

## Validation

- `git diff --check` (passes)
- `python scripts/check_repo_docs.py` (passes)
- `python scripts/check_repo_contracts.py --mode diff <changed files>` (passes)
- `cd ai-pic-frontend && npx tsx --test tests/storyOutlineSection.test.tsx` (2 passing)
- `cd ai-pic-frontend && npm run lint` (passes with 3 existing warnings)
- `cd ai-pic-frontend && npm test` (441 passing, 9 failing in unrelated existing Production Canvas suites; failures are in `productionCanvasChatBar.test.tsx` and `productionCanvasPlanner.test.tsx`, while the new story outline suite passes)
- Production build was not run because this is an isolated client-component rendering change with no route, layout, auth, config, SSR, or hydration contract change.
- Chrome real-browser entry: `http://localhost:8090/stories/cc05f0658ea8494c80676ca074c1adaa`.
- New-story browser result: the page rendered the `故事大纲` heading and every populated structured contract section, including target audience, core pain, protagonist goal, stage expectations, stage highs, and traffic hooks.
- Legacy-story boundary check: `http://localhost:8090/stories/0e0c922a67b44a0c9f51650cc6ef3e59` rendered without a `故事大纲` section, as requested.
- Browser console evidence: no warnings or errors on either story detail path.

## Next Steps

- None for this scoped change. Historical stories remain unchanged unless a separate migration or fallback display is requested.

## Linked Commits

- This commit.
