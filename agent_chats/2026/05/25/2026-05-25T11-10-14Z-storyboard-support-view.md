---
id: 2026-05-25T11-10-14Z-storyboard-support-view
date: "2026-05-25T11:10:14Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, timeline, storyboard, browser]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceController.ts
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceActiveTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardSupportModel.ts
  - ai-pic-frontend/tests/timelineWorkspaceHelpers.test.ts
  - tasks.md
summary: "Convert the workspace storyboard tab into a timeline support view"
---

## User Prompt

- “继续，验证时可以使用 3D 或 2D 卡通 ，避免平台的真人限制”

## Goals

- Keep storyboard inside the episode workspace as a support view instead of a
  primary orchestration/editor surface.
- Show timeline-aligned placeholders, keyframe/video asset links, and scene
  context.
- Avoid real-person validation assumptions; future generation validation should
  use 2D or 3D cartoon style prompts.

## Changes

- Removed the embedded legacy `StoryboardEditor` from the episode workspace
  storyboard tab.
- Added a storyboard support model that summarizes frame, keyframe, video,
  source, and Timeline metadata.
- Rebuilt the storyboard tab as a read-only aligned frame list with context and
  asset links back to the Timeline workspace.
- Passed selected storyboard and normalized scenes into the storyboard support
  tab.
- Updated the episode workspace header so the storyboard step opens the support
  view instead of presenting a generation action.
- Added frontend tests for the support-view frame/summary model.
- Marked the task-board storyboard support-view item complete.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npm run test`
  - Result: passed, 22 tests.
- `cd ai-pic-frontend && npm run lint`
  - Result: passed with 18 existing warnings and 0 errors.
- `cd ai-pic-frontend && npm run build`
  - Result: passed.
- `python scripts/check_repo_docs.py`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff 'ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx' ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceController.ts ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx ai-pic-frontend/src/components/features/episode/WorkspaceActiveTabContent.tsx ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardSupportModel.ts ai-pic-frontend/tests/timelineWorkspaceHelpers.test.ts tasks.md agent_chats/2026/05/25/2026-05-25T11-10-14Z-storyboard-support-view.md`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `pre-commit run --files 'ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx' ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceController.ts ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx ai-pic-frontend/src/components/features/episode/WorkspaceActiveTabContent.tsx ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardSupportModel.ts ai-pic-frontend/tests/timelineWorkspaceHelpers.test.ts tasks.md agent_chats/2026/05/25/2026-05-25T11-10-14Z-storyboard-support-view.md`
  - Result: passed on rerun after `prettier` formatting, including frontend
    lint.

2. Browser validation:

- Engine: Codex in-app Browser (`iab`), not Chrome.
- Entry URL:
  `http://localhost:8089/episodes/133/workspace?tab=storyboard&scriptId=117`
- Result: support view loaded with `分镜辅助工作区`, `占位帧`,
  `关键帧 / 视频`, and `返回时间轴`; old generation/editor markers
  `生成分镜`, `StoryboardEditor`, `保存`, and `预览提示词` were absent.
- Console: 0 warnings/errors read through Browser.
- Evidence:
  `artifacts/runs/frontend-storyboard-support-view-iab-20260525T111014Z/browser-validation.json`
  and
  `artifacts/runs/frontend-storyboard-support-view-iab-20260525T111014Z/storyboard-support-view.png`.

## Next Steps

- Continue legacy cleanup around `scripts_legacy.py`,
  `dialogue_audio_service.py`, and `ai_service_manager.py`.
- Start the 10-sample proof with a fixed 2D/3D cartoon vertical so provider
  safety restrictions around realistic people do not dominate the signal.

## Linked Commits

- Pending
