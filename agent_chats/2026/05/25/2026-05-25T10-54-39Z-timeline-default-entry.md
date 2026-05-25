---
id: 2026-05-25T10-54-39Z-timeline-default-entry
date: "2026-05-25T10:54:39Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, timeline, legacy, browser]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineMainPanel.tsx
  - ai-pic-frontend/src/components/features/script/ScriptHeader.tsx
  - ai-pic-frontend/src/components/features/script/WorkflowSteps.tsx
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
  - tasks.md
summary: "Route default production entry points to the timeline workspace"
---

## User Prompt

- “按项目规范，依次完成对应计划，保证原子性提交”
- “使用你的内置浏览器”
- “继续”

## Goals

- Keep the episode workspace as the single default production surface.
- Stop script/story production entry points from treating storyboard as the
  default orchestration tab.
- Preserve storyboard as a support view reachable from the timeline workspace.

## Changes

- Updated the script detail header secondary action from storyboard navigation
  to timeline workspace navigation.
- Updated the script detail production step from standalone storyboard
  management to timeline-main-chain support.
- Routed the story-detail storyboard helper to the timeline tab for default
  production entry.
- Fixed the timeline model selector type boundary surfaced by `next build` by
  allowing model options without a duplicate `id` when `model_id` is present.
- Marked the task-board item complete with current wording because the old
  standalone storyboard page path no longer exists.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npm run test`
  - Result: passed, 19 tests.
- `cd ai-pic-frontend && npm run lint`
  - Result: passed with 18 existing warnings and 0 errors.
- `cd ai-pic-frontend && npm run build`
  - Initial result: failed on an existing `AIModel[]` to `ModelOption[]` type
    mismatch in `EpisodeTimelineWorkspace`.
  - Fix: normalized `EpisodeTimelineMainPanel` model option typing to accept
    `model_id` without requiring a duplicate `id`.
  - Rerun result: passed.
- `python scripts/check_repo_docs.py`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff 'ai-pic-frontend/src/app/scripts/[id]/page.tsx' ai-pic-frontend/src/components/features/script/ScriptHeader.tsx ai-pic-frontend/src/components/features/script/WorkflowSteps.tsx ai-pic-frontend/src/hooks/useStoryDetail.ts ai-pic-frontend/src/components/features/episode/EpisodeTimelineMainPanel.tsx tasks.md agent_chats/2026/05/25/2026-05-25T10-54-39Z-timeline-default-entry.md`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `pre-commit run --files 'ai-pic-frontend/src/app/scripts/[id]/page.tsx' ai-pic-frontend/src/components/features/episode/EpisodeTimelineMainPanel.tsx ai-pic-frontend/src/components/features/script/ScriptHeader.tsx ai-pic-frontend/src/components/features/script/WorkflowSteps.tsx ai-pic-frontend/src/hooks/useStoryDetail.ts tasks.md agent_chats/2026/05/25/2026-05-25T10-54-39Z-timeline-default-entry.md`
  - Result: passed on rerun after `prettier` formatting, including frontend
    lint.

2. Browser validation:

- Engine: Codex in-app Browser (`iab`), not Chrome.
- Entry URL: `http://localhost:8089/scripts/117`
- Login: test account from `AGENTS.md`.
- User path: open script detail, confirm `进入时间轴` is present and
  `打开分镜` is absent, click `进入时间轴`.
- Final URL:
  `http://localhost:8089/episodes/133/workspace?tab=timeline&scriptId=117`
- Result: timeline workspace loaded with `时间轴主画布`; console warnings/errors
  read through Browser were 0.
- Evidence:
  `artifacts/runs/frontend-timeline-entry-iab-20260525T105439Z/browser-validation.json`
  and
  `artifacts/runs/frontend-timeline-entry-iab-20260525T105439Z/timeline-entry.png`.

## Next Steps

- Continue legacy cleanup around `scripts_legacy.py`,
  `dialogue_audio_service.py`, and `ai_service_manager.py`.

## Linked Commits

- Pending
